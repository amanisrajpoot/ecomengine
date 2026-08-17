"""Order HTTP routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import AuthContext, require_permission, resolve_tenant_id
from app.core.errors import AppError
from app.identity.rbac import Role
from app.orders import service
from app.orders.schemas import (
    OrderCheckout,
    OrderDetail,
    OrderRead,
    OrderTransition,
)

router = APIRouter(prefix="/orders", tags=["orders"])


def _require_tenant(tenant_id: uuid.UUID | None) -> uuid.UUID:
    if tenant_id is None:
        raise AppError("TENANT_REQUIRED", "X-Tenant-ID header is required", 400)
    return tenant_id


def _customer_scope(ctx: AuthContext) -> uuid.UUID | None:
    is_super = any(b.role == Role.SUPER_ADMIN.value for b in ctx.roles)
    if is_super:
        return None
    user_roles = {b.role for b in ctx.roles}
    if Role.CUSTOMER.value in user_roles and not user_roles.intersection(
        {
            Role.TENANT_ADMIN.value,
            Role.BUSINESS_OWNER.value,
            Role.BUSINESS_MANAGER.value,
            Role.STAFF.value,
        }
    ):
        return ctx.user.id
    return None


def _order_to_read(order) -> OrderRead:
    return OrderRead.model_validate(order)


def _order_to_detail(order) -> OrderDetail:
    return OrderDetail.model_validate(order)


@router.post("/checkout", response_model=OrderRead)
async def checkout_order(
    payload: OrderCheckout,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("orders.place")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> OrderRead:
    tid = _require_tenant(tenant_id)
    order = await service.checkout_from_cart(
        db,
        tenant_id=tid,
        customer_id=ctx.user.id,
        payload=payload,
    )
    return _order_to_read(order)


@router.get("/{order_id}", response_model=OrderDetail)
async def get_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("orders.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> OrderDetail:
    tid = _require_tenant(tenant_id)
    order = await service.get_order(
        db,
        tenant_id=tid,
        order_id=order_id,
        customer_id=_customer_scope(ctx),
    )
    return _order_to_detail(order)


@router.get("", response_model=list[OrderRead])
async def list_orders(
    business_id: uuid.UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("orders.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[OrderRead]:
    tid = _require_tenant(tenant_id)
    rows = await service.list_orders(
        db,
        tenant_id=tid,
        customer_id=_customer_scope(ctx),
        business_id=business_id,
        status=status,
    )
    return [_order_to_read(r) for r in rows]


@router.post("/{order_id}/transition", response_model=OrderDetail)
async def transition_order(
    order_id: uuid.UUID,
    payload: OrderTransition,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("orders.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> OrderDetail:
    tid = _require_tenant(tenant_id)
    order = await service.transition_order(
        db,
        tenant_id=tid,
        order_id=order_id,
        payload=payload,
        actor_user_id=ctx.user.id,
    )
    return _order_to_detail(order)
