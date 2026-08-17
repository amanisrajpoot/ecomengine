"""Payment capture, refunds, and order integration."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.orders.schemas import OrderTransition
from app.orders.service import get_order, transition_order
from app.payments.gateway import PaymentStatus, get_gateway
from app.payments.models import Payment, Refund
from app.payments.schemas import PaymentCreate, RefundCreate


async def _get_payment(
    db: AsyncSession, *, tenant_id: uuid.UUID, payment_id: uuid.UUID
) -> Payment:
    payment = await db.scalar(
        select(Payment).where(Payment.id == payment_id, Payment.tenant_id == tenant_id)
    )
    if not payment:
        raise AppError("PAYMENT_NOT_FOUND", "Payment not found", status_code=404)
    return payment


async def _confirm_order_payment(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    order_id: uuid.UUID,
    actor_user_id: uuid.UUID | None,
) -> None:
    order = await get_order(db, tenant_id=tenant_id, order_id=order_id)
    if order.status == "PAYMENT_PENDING":
        await transition_order(
            db,
            tenant_id=tenant_id,
            order_id=order_id,
            payload=OrderTransition(to_status="PAYMENT_CONFIRMED", reason="payment captured"),
            actor_user_id=actor_user_id,
        )


async def create_payment_for_order(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    order_id: uuid.UUID,
    customer_id: uuid.UUID,
    payload: PaymentCreate,
    idempotency_key: str | None = None,
) -> tuple[Payment, dict | None]:
    if idempotency_key:
        existing = await db.scalar(
            select(Payment).where(
                Payment.tenant_id == tenant_id,
                Payment.idempotency_key == idempotency_key,
            )
        )
        if existing:
            client_payload = existing.raw.get("client_payload")
            return existing, client_payload

    order = await get_order(
        db, tenant_id=tenant_id, order_id=order_id, customer_id=customer_id
    )
    if order.status != "PAYMENT_PENDING":
        raise AppError(
            "ORDER_NOT_AWAITING_PAYMENT",
            f"Order status {order.status} cannot accept payment",
            status_code=400,
        )

    total_paise = int(order.pricing_snapshot.get("total_paise", 0))
    if total_paise <= 0:
        raise AppError("INVALID_ORDER_AMOUNT", "Order total must be positive", status_code=400)

    gateway = get_gateway(payload.provider.value)
    init = await gateway.initiate(
        amount_paise=total_paise,
        currency=order.currency,
        order_id=str(order_id),
    )

    raw: dict = {}
    if init.client_payload:
        raw["client_payload"] = init.client_payload

    payment = Payment(
        tenant_id=tenant_id,
        order_id=order_id,
        provider=payload.provider.value,
        provider_ref=init.provider_ref,
        status=init.status.value,
        amount_paise=total_paise,
        currency=order.currency,
        idempotency_key=idempotency_key,
        raw=raw,
    )
    db.add(payment)
    await db.flush()

    client_payload = init.client_payload

    if payload.provider.value == "COD":
        captured_status = await gateway.capture(
            provider_ref=payment.provider_ref, amount_paise=total_paise
        )
        payment.status = captured_status.value
        await db.flush()
        await _confirm_order_payment(
            db, tenant_id=tenant_id, order_id=order_id, actor_user_id=customer_id
        )

    await db.commit()
    await db.refresh(payment)
    return payment, client_payload


async def capture_payment(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    payment_id: uuid.UUID,
    actor_user_id: uuid.UUID | None = None,
) -> Payment:
    payment = await _get_payment(db, tenant_id=tenant_id, payment_id=payment_id)
    if payment.status == PaymentStatus.CAPTURED.value:
        return payment
    if payment.status not in {PaymentStatus.PENDING.value, PaymentStatus.CREATED.value}:
        raise AppError(
            "PAYMENT_NOT_CAPTURABLE",
            f"Payment status {payment.status} cannot be captured",
            status_code=400,
        )

    gateway = get_gateway(payment.provider)
    captured_status = await gateway.capture(
        provider_ref=payment.provider_ref,
        amount_paise=payment.amount_paise,
    )
    payment.status = captured_status.value
    await db.flush()
    await _confirm_order_payment(
        db,
        tenant_id=tenant_id,
        order_id=payment.order_id,
        actor_user_id=actor_user_id,
    )
    await db.commit()
    await db.refresh(payment)
    return payment


async def get_payment(
    db: AsyncSession, *, tenant_id: uuid.UUID, payment_id: uuid.UUID
) -> Payment:
    return await _get_payment(db, tenant_id=tenant_id, payment_id=payment_id)


async def list_payments_for_order(
    db: AsyncSession, *, tenant_id: uuid.UUID, order_id: uuid.UUID
) -> list[Payment]:
    stmt = select(Payment).where(
        Payment.tenant_id == tenant_id,
        Payment.order_id == order_id,
    )
    stmt = stmt.order_by(Payment.created_at.desc())
    return list(await db.scalars(stmt))


async def create_refund(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    payment_id: uuid.UUID,
    payload: RefundCreate,
    actor_user_id: uuid.UUID | None = None,
) -> Refund:
    _ = actor_user_id
    payment = await _get_payment(db, tenant_id=tenant_id, payment_id=payment_id)
    if payment.status != PaymentStatus.CAPTURED.value:
        raise AppError(
            "PAYMENT_NOT_REFUNDABLE",
            "Only captured payments can be refunded",
            status_code=400,
        )

    amount = payload.amount_paise if payload.amount_paise is not None else payment.amount_paise
    if amount <= 0 or amount > payment.amount_paise:
        raise AppError("INVALID_REFUND_AMOUNT", "Invalid refund amount", status_code=400)

    existing_refunded = sum(
        r.amount_paise
        for r in await db.scalars(
            select(Refund).where(
                Refund.payment_id == payment.id,
                Refund.status == "COMPLETED",
            )
        )
    )
    if existing_refunded + amount > payment.amount_paise:
        raise AppError(
            "REFUND_EXCEEDS_PAYMENT",
            "Refund total would exceed payment amount",
            status_code=400,
        )

    refund = Refund(
        tenant_id=tenant_id,
        payment_id=payment.id,
        order_id=payment.order_id,
        amount_paise=amount,
        status="COMPLETED",
        reason=payload.reason,
    )
    db.add(refund)
    if existing_refunded + amount >= payment.amount_paise:
        payment.status = PaymentStatus.REFUNDED.value

    await db.commit()
    await db.refresh(refund)
    return refund
