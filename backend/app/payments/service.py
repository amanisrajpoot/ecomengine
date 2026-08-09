"""Payment orchestration service."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.orders.models import Order
from app.orders.schemas import OrderTransitionRequest
from app.orders.service import get_order, transition_order
from app.payments.models import Payment, Refund
from app.payments.registry import gateway_registry
from app.payments.schemas import (
    CreatePaymentRequest,
    InitiatePaymentBody,
    RefundBody,
    RefundPaymentRequest,
    VerifyPaymentBody,
    VerifyPaymentRequest,
)


async def _get_order(db: AsyncSession, *, tenant_id: uuid.UUID, order_id: uuid.UUID) -> Order:
    order = await db.scalar(
        select(Order).where(Order.id == order_id, Order.tenant_id == tenant_id)
    )
    if not order:
        raise AppError("ORDER_NOT_FOUND", "Order not found", 404)
    return order


async def initiate_payment(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    order_id: uuid.UUID,
    payload: InitiatePaymentBody,
    actor_user_id: uuid.UUID | None,
) -> tuple[Payment, Order]:
    order = await _get_order(db, tenant_id=tenant_id, order_id=order_id)
    if order.status not in {"CREATED", "PAYMENT_PENDING"}:
        raise AppError(
            "ORDER_NOT_PAYABLE",
            f"Order status {order.status} cannot initiate payment",
            status_code=409,
        )

    amount = int(order.pricing_snapshot.get("total_paise") or 0)
    if amount <= 0:
        raise AppError("INVALID_ORDER_AMOUNT", "Order total must be > 0", 400)

    if payload.idempotency_key:
        existing = await db.scalar(
            select(Payment).where(
                Payment.tenant_id == tenant_id,
                Payment.idempotency_key == payload.idempotency_key,
            )
        )
        if existing:
            return existing, order

    gateway = gateway_registry.get(payload.provider)
    result = await gateway.create_payment(
        CreatePaymentRequest(
            order_id=str(order.id),
            amount_paise=amount,
            currency=order.currency,
            customer_id=str(order.customer_id),
            customer_phone=payload.customer_phone,
            customer_email=payload.customer_email,
            return_url=payload.return_url,
            notify_url=payload.notify_url,
            idempotency_key=payload.idempotency_key or str(order.id),
            metadata={"tenant_id": str(tenant_id)},
        )
    )

    payment = Payment(
        tenant_id=tenant_id,
        order_id=order.id,
        provider=result.provider,
        provider_ref=result.provider_ref,
        status=result.status,
        amount_paise=amount,
        currency=order.currency,
        idempotency_key=payload.idempotency_key or str(order.id),
        raw=result.raw,
        checkout_payload=result.checkout,
    )
    db.add(payment)

    # Align order payment_method for reporting.
    order.payment_method = "COD" if payload.provider == "cod" else "ONLINE"
    await db.commit()
    await db.refresh(payment)
    await db.refresh(order)

    # Move CREATED → PAYMENT_PENDING for online; COD → PAYMENT_CONFIRMED.
    if payload.provider == "cod":
        order_graph = await transition_order(
            db,
            tenant_id=tenant_id,
            order_id=order.id,
            payload=OrderTransitionRequest(
                to_status="PAYMENT_CONFIRMED",
                actor="payments",
                reason="cod_authorized",
            ),
            actor_user_id=actor_user_id,
        )
        payment.status = "AUTHORIZED"
        await db.commit()
        await db.refresh(payment)

        from app.ledger.service import post_payment_captured

        await post_payment_captured(
            db, tenant_id=tenant_id, order=order_graph[0], payment=payment
        )
        return payment, order_graph[0]

    if order.status == "CREATED":
        order_graph = await transition_order(
            db,
            tenant_id=tenant_id,
            order_id=order.id,
            payload=OrderTransitionRequest(
                to_status="PAYMENT_PENDING",
                actor="payments",
                reason=f"{payload.provider}_initiated",
            ),
            actor_user_id=actor_user_id,
        )
        return payment, order_graph[0]

    return payment, order


async def verify_and_confirm(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    order_id: uuid.UUID,
    payload: VerifyPaymentBody,
    actor_user_id: uuid.UUID | None,
) -> tuple[Payment, Order]:
    order = await _get_order(db, tenant_id=tenant_id, order_id=order_id)
    payment = await db.scalar(
        select(Payment)
        .where(Payment.order_id == order.id, Payment.tenant_id == tenant_id)
        .order_by(Payment.created_at.desc())
    )
    if not payment:
        raise AppError("PAYMENT_NOT_FOUND", "No payment found for order", 404)

    provider = payload.provider or payment.provider
    provider_ref = payload.provider_ref or payment.provider_ref
    if not provider_ref:
        raise AppError("PROVIDER_REF_REQUIRED", "provider_ref is required", 400)

    gateway = gateway_registry.get(provider)
    result = await gateway.verify_payment(
        VerifyPaymentRequest(provider_ref=provider_ref, payload=payload.payload)
    )
    payment.status = result.status
    payment.provider_ref = result.provider_ref
    payment.raw = {**(payment.raw or {}), "verify": result.raw}
    await db.commit()
    await db.refresh(payment)

    if result.status == "CAPTURED" and order.status in {"CREATED", "PAYMENT_PENDING"}:
        await transition_order(
            db,
            tenant_id=tenant_id,
            order_id=order.id,
            payload=OrderTransitionRequest(
                to_status="PAYMENT_CONFIRMED",
                actor="payments",
                reason=f"{provider}_captured",
            ),
            actor_user_id=actor_user_id,
        )
        order = (await get_order(db, tenant_id=tenant_id, order_id=order.id))[0]

        from app.ledger.service import post_payment_captured

        await post_payment_captured(
            db, tenant_id=tenant_id, order=order, payment=payment
        )

    return payment, order


async def refund_payment(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    payment_id: uuid.UUID,
    payload: RefundBody,
    actor_user_id: uuid.UUID | None,
) -> Refund:
    _ = actor_user_id
    payment = await db.scalar(
        select(Payment).where(Payment.id == payment_id, Payment.tenant_id == tenant_id)
    )
    if not payment:
        raise AppError("PAYMENT_NOT_FOUND", "Payment not found", 404)
    if payload.amount_paise > payment.amount_paise:
        raise AppError("REFUND_EXCEEDS_PAYMENT", "Refund exceeds payment amount", 400)
    if not payment.provider_ref:
        raise AppError("PROVIDER_REF_REQUIRED", "Payment has no provider_ref", 400)

    gateway = gateway_registry.get(payment.provider)
    result = await gateway.refund_payment(
        RefundPaymentRequest(
            provider_ref=payment.provider_ref,
            amount_paise=payload.amount_paise,
            reason=payload.reason,
            idempotency_key=payload.idempotency_key,
        )
    )
    refund = Refund(
        tenant_id=tenant_id,
        payment_id=payment.id,
        order_id=payment.order_id,
        provider_ref=result.provider_ref,
        amount_paise=result.amount_paise,
        status=result.status,
        reason=payload.reason,
        raw=result.raw,
    )
    db.add(refund)
    await db.commit()
    await db.refresh(refund)

    from app.ledger.service import post_payment_refund

    await post_payment_refund(
        db, tenant_id=tenant_id, payment=payment, refund=refund
    )
    return refund


async def list_payments_for_order(
    db: AsyncSession, *, tenant_id: uuid.UUID, order_id: uuid.UUID
) -> list[Payment]:
    await _get_order(db, tenant_id=tenant_id, order_id=order_id)
    return list(
        await db.scalars(
            select(Payment)
            .where(Payment.tenant_id == tenant_id, Payment.order_id == order_id)
            .order_by(Payment.created_at.desc())
        )
    )


async def handle_cashfree_webhook(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID | None,
    payload: dict,
) -> Payment | None:
    """Best-effort webhook handler. Looks up payment by Cashfree order_id."""
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    order_obj = data.get("order") if isinstance(data.get("order"), dict) else data
    provider_ref = str(order_obj.get("order_id") or payload.get("order_id") or "")
    if not provider_ref:
        return None
    payment = await db.scalar(
        select(Payment).where(Payment.provider == "cashfree", Payment.provider_ref == provider_ref)
    )
    if not payment:
        return None
    if tenant_id and payment.tenant_id != tenant_id:
        raise AppError("FORBIDDEN_TENANT", "Webhook tenant mismatch", 403)

    status_hint = str(
        order_obj.get("order_status")
        or data.get("payment_status")
        or payload.get("type")
        or ""
    ).upper()
    mock_status = "CAPTURED" if status_hint in {"PAID", "SUCCESS", "PAYMENT_SUCCESS"} else None
    verify_payload = {"status": mock_status} if mock_status else payload
    if mock_status is None and "PAID" in status_hint:
        verify_payload = {"mock_status": "CAPTURED"}

    payment, _order = await verify_and_confirm(
        db,
        tenant_id=payment.tenant_id,
        order_id=payment.order_id,
        payload=VerifyPaymentBody(
            provider="cashfree",
            provider_ref=provider_ref,
            payload=verify_payload if mock_status else {"mock_status": "CAPTURED", **payload},
        ),
        actor_user_id=None,
    )
    return payment
