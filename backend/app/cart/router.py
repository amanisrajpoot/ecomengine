"""Cart HTTP routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.cart import service
from app.cart.schemas import (
    CartCreate,
    CartItemCreate,
    CartItemRead,
    CartItemUpdate,
    CartRead,
    CartWithPricing,
)
from app.core.db import get_db
from app.core.deps import AuthContext, require_permission, resolve_tenant_id
from app.core.errors import AppError
from app.identity.rbac import Role
from app.pricing.schemas import PriceBreakdown

router = APIRouter(prefix="/carts", tags=["carts"])


def _require_tenant(tenant_id: uuid.UUID | None) -> uuid.UUID:
    if tenant_id is None:
        raise AppError("TENANT_REQUIRED", "X-Tenant-ID header is required", 400)
    return tenant_id


def _customer_scope(ctx: AuthContext) -> uuid.UUID | None:
    is_super = any(b.role == Role.SUPER_ADMIN.value for b in ctx.roles)
    if is_super:
        return None
    return ctx.user.id


def _cart_to_read(cart) -> CartRead:
    return CartRead(
        id=cart.id,
        tenant_id=cart.tenant_id,
        customer_id=cart.customer_id,
        business_id=cart.business_id,
        location_id=cart.location_id,
        currency=cart.currency,
        pricing_snapshot=cart.pricing_snapshot,
        created_at=cart.created_at,
        updated_at=cart.updated_at,
        items=[CartItemRead.model_validate(i) for i in cart.items],
    )


@router.post("", response_model=CartRead)
async def create_cart(
    payload: CartCreate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("cart.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> CartRead:
    tid = _require_tenant(tenant_id)
    cart = await service.create_cart(
        db,
        tenant_id=tid,
        customer_id=ctx.user.id,
        payload=payload,
    )
    return _cart_to_read(cart)


@router.get("/{cart_id}", response_model=CartRead)
async def get_cart(
    cart_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("cart.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> CartRead:
    tid = _require_tenant(tenant_id)
    cart = await service.get_cart(
        db,
        tenant_id=tid,
        cart_id=cart_id,
        customer_id=_customer_scope(ctx),
    )
    return _cart_to_read(cart)


@router.post("/{cart_id}/items", response_model=CartRead)
async def add_cart_item(
    cart_id: uuid.UUID,
    payload: CartItemCreate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("cart.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> CartRead:
    tid = _require_tenant(tenant_id)
    cart = await service.add_cart_item(
        db,
        tenant_id=tid,
        cart_id=cart_id,
        customer_id=ctx.user.id,
        payload=payload,
    )
    return _cart_to_read(cart)


@router.patch("/{cart_id}/items/{item_id}", response_model=CartRead)
async def update_cart_item(
    cart_id: uuid.UUID,
    item_id: uuid.UUID,
    payload: CartItemUpdate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("cart.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> CartRead:
    tid = _require_tenant(tenant_id)
    cart = await service.update_cart_item(
        db,
        tenant_id=tid,
        cart_id=cart_id,
        item_id=item_id,
        customer_id=ctx.user.id,
        payload=payload,
    )
    return _cart_to_read(cart)


@router.delete("/{cart_id}/items/{item_id}", response_model=CartRead)
async def remove_cart_item(
    cart_id: uuid.UUID,
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("cart.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> CartRead:
    tid = _require_tenant(tenant_id)
    cart = await service.remove_cart_item(
        db,
        tenant_id=tid,
        cart_id=cart_id,
        item_id=item_id,
        customer_id=ctx.user.id,
    )
    return _cart_to_read(cart)


@router.post("/{cart_id}/price", response_model=CartWithPricing)
async def price_cart(
    cart_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("cart.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> CartWithPricing:
    tid = _require_tenant(tenant_id)
    cart, _ = await service.recalculate_cart_pricing(
        db,
        tenant_id=tid,
        cart_id=cart_id,
        customer_id=_customer_scope(ctx),
    )
    pricing = None
    if cart.pricing_snapshot:
        pricing = PriceBreakdown.model_validate(cart.pricing_snapshot)
    return CartWithPricing(
        **(_cart_to_read(cart).model_dump()),
        pricing=pricing,
    )
