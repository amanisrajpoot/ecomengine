"""Order HTTP routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import AuthContext, require_permission, resolve_tenant_id
from app.core.errors import AppError
from app.orders import service
from app.orders.schemas import (
    CheckoutRequest,
    OrderDebuggerRead,
    OrderItemRead,
    OrderRead,
    OrderStatusEventRead,
    OrderTransitionRequest,
)

router = APIRouter(prefix="/orders", tags=["orders"])


def _require_tenant(tenant_id: uuid.UUID | None) -> uuid.UUID:
    if tenant_id is None:
        raise AppError("TENANT_REQUIRED", "X-Tenant-ID header is required", 400)
    return tenant_id


def _to_order_read(order, items, events) -> OrderRead:
    data = OrderRead.model_validate(order)
    data.items = [OrderItemRead.model_validate(i) for i in items]
    data.status_events = [OrderStatusEventRead.model_validate(e) for e in events]
    return data


@router.post("/checkout", response_model=OrderRead)
async def checkout(
    payload: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("orders.create")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> OrderRead:
    tid = _require_tenant(tenant_id)
    order, items, events = await service.checkout_from_cart(
        db, tenant_id=tid, user_id=ctx.user.id, payload=payload
    )
    return _to_order_read(order, items, events)


@router.get("", response_model=list[OrderRead])
async def list_orders(
    business_id: uuid.UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("orders.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[OrderRead]:
    _ = ctx
    tid = _require_tenant(tenant_id)
    orders = await service.list_orders(
        db, tenant_id=tid, business_id=business_id, status=status
    )
    result: list[OrderRead] = []
    for order in orders:
        full = await service.get_order(db, tenant_id=tid, order_id=order.id)
        result.append(_to_order_read(*full))
    return result


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("orders.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> OrderRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    order, items, events = await service.get_order(
        db, tenant_id=tid, order_id=order_id
    )
    return _to_order_read(order, items, events)


@router.get("/{order_id}/debugger", response_model=OrderDebuggerRead)
async def get_order_debugger(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("orders.debug")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> OrderDebuggerRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    return await service.get_order_debugger(db, tenant_id=tid, order_id=order_id)


@router.post("/{order_id}/transitions", response_model=OrderRead)
async def transition_order(
    order_id: uuid.UUID,
    payload: OrderTransitionRequest,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("orders.transition")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> OrderRead:
    tid = _require_tenant(tenant_id)
    order, items, events = await service.transition_order(
        db,
        tenant_id=tid,
        order_id=order_id,
        payload=payload,
        actor_user_id=ctx.user.id,
    )
    return _to_order_read(order, items, events)
