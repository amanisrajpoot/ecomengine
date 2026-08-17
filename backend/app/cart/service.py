from __future__ import annotations

"""Cart aggregate service."""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.businesses.service import get_business
from app.cart.models import Cart, CartItem
from app.cart.schemas import CartCreate, CartItemCreate, CartItemUpdate
from app.core.errors import AppError
from app.locations.service import get_location
from app.pricing.service import calculate_cart_breakdown


async def _get_cart(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    cart_id: uuid.UUID,
    customer_id: uuid.UUID | None = None,
) -> Cart:
    cart = await db.scalar(
        select(Cart)
        .options(selectinload(Cart.items))
        .where(Cart.id == cart_id, Cart.tenant_id == tenant_id)
    )
    if not cart:
        raise AppError("CART_NOT_FOUND", "Cart not found", status_code=404)
    if customer_id is not None and cart.customer_id != customer_id:
        raise AppError("FORBIDDEN", "Cart does not belong to this customer", status_code=403)
    return cart


async def create_cart(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    payload: CartCreate,
) -> Cart:
    await get_business(db, tenant_id=tenant_id, business_id=payload.business_id)
    if payload.location_id is not None:
        await get_location(
            db,
            tenant_id=tenant_id,
            business_id=payload.business_id,
            location_id=payload.location_id,
        )
    cart = Cart(
        tenant_id=tenant_id,
        customer_id=customer_id,
        business_id=payload.business_id,
        location_id=payload.location_id,
        currency=payload.currency,
        pricing_snapshot={},
    )
    db.add(cart)
    await db.commit()
    await db.refresh(cart)
    return await _get_cart(db, tenant_id=tenant_id, cart_id=cart.id)


async def get_cart(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    cart_id: uuid.UUID,
    customer_id: uuid.UUID | None = None,
) -> Cart:
    return await _get_cart(
        db, tenant_id=tenant_id, cart_id=cart_id, customer_id=customer_id
    )


async def add_cart_item(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    cart_id: uuid.UUID,
    customer_id: uuid.UUID,
    payload: CartItemCreate,
) -> Cart:
    cart = await _get_cart(
        db, tenant_id=tenant_id, cart_id=cart_id, customer_id=customer_id
    )
    if cart.business_id is None:
        raise AppError("CART_INCOMPLETE", "Cart has no business context", status_code=400)

    business = await get_business(db, tenant_id=tenant_id, business_id=cart.business_id)
    unit_price_paise = 0
    if payload.meta.get("line_type") == "COURIER_QUOTE":
        if business.type != "COURIER":
            raise AppError(
                "NOT_COURIER_BUSINESS",
                "Courier quote lines require a COURIER business cart",
                status_code=400,
            )
        unit_price_paise = int(payload.meta["quoted_paise"])

    item = CartItem(
        cart_id=cart.id,
        variant_id=payload.variant_id,
        bundle_id=payload.bundle_id,
        quantity=payload.quantity,
        addons=[a.model_dump(mode="json") for a in payload.addons],
        meta=payload.meta,
        unit_price_paise=unit_price_paise,
    )
    db.add(item)
    await db.flush()
    await db.refresh(cart, attribute_names=["items"])
    await _refresh_cart_pricing(db, cart=cart)
    await db.commit()
    return await _get_cart(db, tenant_id=tenant_id, cart_id=cart.id)


async def update_cart_item(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    cart_id: uuid.UUID,
    item_id: uuid.UUID,
    customer_id: uuid.UUID,
    payload: CartItemUpdate,
) -> Cart:
    cart = await _get_cart(
        db, tenant_id=tenant_id, cart_id=cart_id, customer_id=customer_id
    )
    item = await db.scalar(
        select(CartItem).where(CartItem.id == item_id, CartItem.cart_id == cart.id)
    )
    if not item:
        raise AppError("CART_ITEM_NOT_FOUND", "Cart item not found", status_code=404)

    data = payload.model_dump(exclude_unset=True)
    if "addons" in data and data["addons"] is not None:
        data["addons"] = [a.model_dump(mode="json") for a in payload.addons or []]
    for key, value in data.items():
        setattr(item, key, value)

    await _refresh_cart_pricing(db, cart=cart)
    await db.commit()
    return await _get_cart(db, tenant_id=tenant_id, cart_id=cart.id)


async def remove_cart_item(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    cart_id: uuid.UUID,
    item_id: uuid.UUID,
    customer_id: uuid.UUID,
) -> Cart:
    cart = await _get_cart(
        db, tenant_id=tenant_id, cart_id=cart_id, customer_id=customer_id
    )
    item = await db.scalar(
        select(CartItem).where(CartItem.id == item_id, CartItem.cart_id == cart.id)
    )
    if not item:
        raise AppError("CART_ITEM_NOT_FOUND", "Cart item not found", status_code=404)
    await db.delete(item)
    await db.flush()
    await db.refresh(cart, attribute_names=["items"])
    await _refresh_cart_pricing(db, cart=cart)
    await db.commit()
    return await _get_cart(db, tenant_id=tenant_id, cart_id=cart.id)


async def recalculate_cart_pricing(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    cart_id: uuid.UUID,
    customer_id: uuid.UUID | None = None,
) -> tuple[Cart, dict]:
    cart = await _get_cart(
        db, tenant_id=tenant_id, cart_id=cart_id, customer_id=customer_id
    )
    breakdown = await _refresh_cart_pricing(db, cart=cart)
    await db.commit()
    refreshed = await _get_cart(db, tenant_id=tenant_id, cart_id=cart.id)
    return refreshed, breakdown.model_dump()


async def _refresh_cart_pricing(db: AsyncSession, *, cart: Cart) -> Any:
    from app.pricing.schemas import PriceBreakdown

    if cart.business_id is None or not cart.items:
        cart.pricing_snapshot = {}
        for item in cart.items:
            item.unit_price_paise = 0
        return PriceBreakdown(
            subtotal_paise=0,
            total_paise=0,
            lines=[],
        )

    breakdown = await calculate_cart_breakdown(
        db,
        tenant_id=cart.tenant_id,
        business_id=cart.business_id,
        items=cart.items,
        location_id=cart.location_id,
    )
    cart.pricing_snapshot = breakdown.model_dump()

    line_by_item: dict[str, int] = {}
    for line in breakdown.lines:
        if line.cart_item_id:
            line_by_item[line.cart_item_id] = line.unit_price_paise

    for item in cart.items:
        item.unit_price_paise = line_by_item.get(str(item.id), item.unit_price_paise)

    return breakdown
