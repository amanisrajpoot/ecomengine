"""Payment HTTP routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import AuthContext, require_permission, resolve_tenant_id
from app.core.errors import AppError
from app.orders import service as orders_service
from app.orders.access import assert_order_readable
from app.payments import service
from app.payments.registry import gateway_registry
from app.payments.schemas import (
    InitiatePaymentBody,
    PaymentInitiateResponse,
    PaymentRead,
    RefundBody,
    RefundRead,
    VerifyPaymentBody,
)

router = APIRouter(tags=["payments"])


def _require_tenant(tenant_id: uuid.UUID | None) -> uuid.UUID:
    if tenant_id is None:
        raise AppError("TENANT_REQUIRED", "X-Tenant-ID header is required", 400)
    return tenant_id


async def _assert_order_payment_access(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    order_id: uuid.UUID,
    ctx: AuthContext,
) -> None:
    order, _, _ = await orders_service.get_order(
        db, tenant_id=tenant_id, order_id=order_id
    )
    await assert_order_readable(db, tenant_id=tenant_id, ctx=ctx, order=order)


@router.get("/payments/providers")
async def list_providers(
    ctx: AuthContext = Depends(require_permission("payments.manage")),
) -> dict[str, list[str]]:
    _ = ctx
    return {"providers": gateway_registry.list_providers()}


@router.post(
    "/orders/{order_id}/payments",
    response_model=PaymentInitiateResponse,
)
async def initiate_payment(
    order_id: uuid.UUID,
    payload: InitiatePaymentBody,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("payments.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> PaymentInitiateResponse:
    tid = _require_tenant(tenant_id)
    await _assert_order_payment_access(db, tenant_id=tid, order_id=order_id, ctx=ctx)
    payment, order = await service.initiate_payment(
        db,
        tenant_id=tid,
        order_id=order_id,
        payload=payload,
        actor_user_id=ctx.user.id,
    )
    return PaymentInitiateResponse(
        payment=PaymentRead.model_validate(payment),
        order_status=order.status,
    )


@router.post(
    "/orders/{order_id}/payments/verify",
    response_model=PaymentInitiateResponse,
)
async def verify_payment(
    order_id: uuid.UUID,
    payload: VerifyPaymentBody,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("payments.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> PaymentInitiateResponse:
    tid = _require_tenant(tenant_id)
    await _assert_order_payment_access(db, tenant_id=tid, order_id=order_id, ctx=ctx)
    payment, order = await service.verify_and_confirm(
        db,
        tenant_id=tid,
        order_id=order_id,
        payload=payload,
        actor_user_id=ctx.user.id,
    )
    return PaymentInitiateResponse(
        payment=PaymentRead.model_validate(payment),
        order_status=order.status,
    )


@router.get("/orders/{order_id}/payments", response_model=list[PaymentRead])
async def list_order_payments(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("payments.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[PaymentRead]:
    tid = _require_tenant(tenant_id)
    await _assert_order_payment_access(db, tenant_id=tid, order_id=order_id, ctx=ctx)
    rows = await service.list_payments_for_order(db, tenant_id=tid, order_id=order_id)
    return [PaymentRead.model_validate(r) for r in rows]


@router.post("/payments/{payment_id}/refunds", response_model=RefundRead)
async def refund_payment(
    payment_id: uuid.UUID,
    payload: RefundBody,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("payments.refund")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> RefundRead:
    tid = _require_tenant(tenant_id)
    refund = await service.refund_payment(
        db,
        tenant_id=tid,
        payment_id=payment_id,
        payload=payload,
        actor_user_id=ctx.user.id,
    )
    return RefundRead.model_validate(refund)


@router.post("/webhooks/cashfree")
async def cashfree_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    payload = await request.json()
    payment = await service.handle_cashfree_webhook(db, tenant_id=None, payload=payload)
    if not payment:
        return {"status": "ignored"}
    return {"status": "ok", "payment_id": str(payment.id)}
