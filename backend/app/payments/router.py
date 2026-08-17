"""Payment HTTP routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import AuthContext, require_permission, resolve_tenant_id
from app.core.errors import AppError
from app.payments import service
from app.payments.schemas import (
    PaymentCreate,
    PaymentInitResponse,
    PaymentRead,
    RefundCreate,
    RefundRead,
)

router = APIRouter(tags=["payments"])


def _require_tenant(tenant_id: uuid.UUID | None) -> uuid.UUID:
    if tenant_id is None:
        raise AppError("TENANT_REQUIRED", "X-Tenant-ID header is required", 400)
    return tenant_id


@router.post("/orders/{order_id}/payments", response_model=PaymentInitResponse)
async def create_payment(
    order_id: uuid.UUID,
    payload: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("payments.create")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> PaymentInitResponse:
    tid = _require_tenant(tenant_id)
    payment, client_payload = await service.create_payment_for_order(
        db,
        tenant_id=tid,
        order_id=order_id,
        customer_id=ctx.user.id,
        payload=payload,
        idempotency_key=idempotency_key,
    )
    return PaymentInitResponse(
        **PaymentRead.model_validate(payment).model_dump(),
        client_payload=client_payload,
    )


@router.get("/orders/{order_id}/payments", response_model=list[PaymentRead])
async def list_order_payments(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("payments.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[PaymentRead]:
    _ = ctx
    tid = _require_tenant(tenant_id)
    rows = await service.list_payments_for_order(db, tenant_id=tid, order_id=order_id)
    return [PaymentRead.model_validate(r) for r in rows]


@router.get("/payments/{payment_id}", response_model=PaymentRead)
async def get_payment(
    payment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("payments.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> PaymentRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    payment = await service.get_payment(db, tenant_id=tid, payment_id=payment_id)
    return PaymentRead.model_validate(payment)


@router.post("/payments/{payment_id}/capture", response_model=PaymentRead)
async def capture_payment(
    payment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("payments.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> PaymentRead:
    tid = _require_tenant(tenant_id)
    payment = await service.capture_payment(
        db, tenant_id=tid, payment_id=payment_id, actor_user_id=ctx.user.id
    )
    return PaymentRead.model_validate(payment)


@router.post("/payments/{payment_id}/refunds", response_model=RefundRead)
async def create_refund(
    payment_id: uuid.UUID,
    payload: RefundCreate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("payments.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> RefundRead:
    tid = _require_tenant(tenant_id)
    refund = await service.create_refund(
        db,
        tenant_id=tid,
        payment_id=payment_id,
        payload=payload,
        actor_user_id=ctx.user.id,
    )
    return RefundRead.model_validate(refund)
