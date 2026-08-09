"""Cart HTTP routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.cart import service
from app.cart.schemas import (
    CartCreate,
    CartFeesUpdate,
    CartItemCreate,
    CartItemRead,
    CartItemUpdate,
    CartRead,
)
from app.core.db import get_db
from app.core.deps import AuthContext, require_permission, resolve_tenant_id
from app.core.errors import AppError

router = APIRouter(prefix="/carts", tags=["carts"])


def _require_tenant(tenant_id: uuid.UUID | None) -> uuid.UUID:
    if tenant_id is None:
        raise AppError("TENANT_REQUIRED", "X-Tenant-ID header is required", 400)
    return tenant_id


def _to_cart_read(cart, items) -> CartRead:
    data = CartRead.model_validate(cart)
    data.items = [CartItemRead.model_validate(i) for i in items]
    return data


@router.post("", response_model=CartRead)
async def create_cart(
    payload: CartCreate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("cart.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> CartRead:
    tid = _require_tenant(tenant_id)
    cart = await service.create_cart(
        db, tenant_id=tid, user_id=ctx.user.id, payload=payload
    )
    _, items = await service.get_cart(db, tenant_id=tid, cart_id=cart.id)
    return _to_cart_read(cart, items)


@router.get("/{cart_id}", response_model=CartRead)
async def get_cart(
    cart_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("cart.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> CartRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    cart, items = await service.get_cart(db, tenant_id=tid, cart_id=cart_id)
    return _to_cart_read(cart, items)


@router.post("/{cart_id}/items", response_model=CartRead)
async def add_item(
    cart_id: uuid.UUID,
    payload: CartItemCreate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("cart.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> CartRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    cart, items = await service.add_item(
        db, tenant_id=tid, cart_id=cart_id, payload=payload
    )
    return _to_cart_read(cart, items)


@router.patch("/{cart_id}/items/{item_id}", response_model=CartRead)
async def update_item(
    cart_id: uuid.UUID,
    item_id: uuid.UUID,
    payload: CartItemUpdate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("cart.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> CartRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    cart, items = await service.update_item(
        db, tenant_id=tid, cart_id=cart_id, item_id=item_id, payload=payload
    )
    return _to_cart_read(cart, items)


@router.delete("/{cart_id}/items/{item_id}", response_model=CartRead)
async def remove_item(
    cart_id: uuid.UUID,
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("cart.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> CartRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    cart, items = await service.remove_item(
        db, tenant_id=tid, cart_id=cart_id, item_id=item_id
    )
    return _to_cart_read(cart, items)


@router.patch("/{cart_id}/fees", response_model=CartRead)
async def update_fees(
    cart_id: uuid.UUID,
    payload: CartFeesUpdate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("cart.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> CartRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    cart, items = await service.update_fees(
        db, tenant_id=tid, cart_id=cart_id, payload=payload
    )
    return _to_cart_read(cart, items)
