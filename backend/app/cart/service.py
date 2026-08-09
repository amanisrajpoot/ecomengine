"""Cart services with pricing snapshot recalculation."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.businesses.service import get_business
from app.cart.models import Cart, CartItem
from app.cart.schemas import CartCreate, CartFeesUpdate, CartItemCreate, CartItemUpdate
from app.catalog.models import Addon, Bundle, Product, Variant
from app.core.errors import AppError
from app.identity.models import CustomerProfile
from app.pricing.engine import price_items
from app.pricing.schemas import PricingContext, PricingInputItem
from app.taxation.schemas import TaxKind
from app.taxation.service import load_rules_for_calculation


async def get_or_create_customer_profile(
    db: AsyncSession, *, tenant_id: uuid.UUID, user_id: uuid.UUID
) -> CustomerProfile:
    profile = await db.scalar(
        select(CustomerProfile).where(
            CustomerProfile.user_id == user_id,
            CustomerProfile.tenant_id == tenant_id,
        )
    )
    if profile:
        return profile
    profile = CustomerProfile(tenant_id=tenant_id, user_id=user_id, display_name=None)
    db.add(profile)
    await db.flush()
    return profile


async def _load_items(db: AsyncSession, cart_id: uuid.UUID) -> list[CartItem]:
    return list(
        await db.scalars(select(CartItem).where(CartItem.cart_id == cart_id).order_by(CartItem.id))
    )


async def _recalculate(db: AsyncSession, cart: Cart) -> Cart:
    items = await _load_items(db, cart.id)
    pricing_items: list[PricingInputItem] = []
    for item in items:
        pricing_items.append(
            PricingInputItem(
                name=item.name_snapshot,
                quantity=item.quantity,
                unit_price_paise=item.unit_price_paise,
                modifiers_paise=item.modifiers_paise,
                variant_id=str(item.variant_id) if item.variant_id else None,
                bundle_id=str(item.bundle_id) if item.bundle_id else None,
                addons=item.addons if isinstance(item.addons, list) else [],
            )
        )
    breakdown = price_items(
        pricing_items,
        PricingContext(
            currency=cart.currency,
            discount_paise=cart.discount_paise,
            delivery_fee_paise=cart.delivery_fee_paise,
            platform_fee_paise=cart.platform_fee_paise,
            other_fees_paise=0,
            tax_rate_bps=500,
            tax_jurisdiction="IN-INTRA",
        ),
        tax_rules=await load_rules_for_calculation(
            db,
            tenant_id=cart.tenant_id,
            kind=TaxKind.CUSTOMER_TRANSACTION.value,
        ),
    )
    cart.pricing_snapshot = breakdown.model_dump(mode="json")
    await db.commit()
    await db.refresh(cart)
    return cart


async def create_cart(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: CartCreate,
) -> Cart:
    await get_business(db, tenant_id=tenant_id, business_id=payload.business_id)
    customer = await get_or_create_customer_profile(db, tenant_id=tenant_id, user_id=user_id)
    cart = Cart(
        tenant_id=tenant_id,
        customer_id=customer.id,
        business_id=payload.business_id,
        location_id=payload.location_id,
        currency="INR",
        pricing_snapshot={},
        discount_paise=payload.discount_paise,
        delivery_fee_paise=payload.delivery_fee_paise,
        platform_fee_paise=payload.platform_fee_paise,
        status="OPEN",
    )
    db.add(cart)
    await db.commit()
    await db.refresh(cart)
    return await _recalculate(db, cart)


async def get_cart(
    db: AsyncSession, *, tenant_id: uuid.UUID, cart_id: uuid.UUID
) -> tuple[Cart, list[CartItem]]:
    cart = await db.scalar(
        select(Cart).where(Cart.id == cart_id, Cart.tenant_id == tenant_id)
    )
    if not cart:
        raise AppError("CART_NOT_FOUND", "Cart not found", 404)
    items = await _load_items(db, cart.id)
    return cart, items


async def add_item(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    cart_id: uuid.UUID,
    payload: CartItemCreate,
) -> tuple[Cart, list[CartItem]]:
    cart, _ = await get_cart(db, tenant_id=tenant_id, cart_id=cart_id)
    if cart.status != "OPEN":
        raise AppError("CART_NOT_OPEN", "Cart is not open", 409)
    if not payload.variant_id and not payload.bundle_id:
        raise AppError("CART_ITEM_INVALID", "variant_id or bundle_id is required", 400)
    if payload.variant_id and payload.bundle_id:
        raise AppError("CART_ITEM_INVALID", "Provide only one of variant_id or bundle_id", 400)

    if payload.variant_id:
        variant = await db.scalar(
            select(Variant).where(
                Variant.id == payload.variant_id, Variant.tenant_id == tenant_id
            )
        )
        if not variant or not variant.is_available:
            raise AppError("VARIANT_NOT_FOUND", "Variant not found or unavailable", 404)
        product = await db.get(Product, variant.product_id)
        if not product or product.business_id != cart.business_id:
            raise AppError("VARIANT_NOT_FOUND", "Variant does not belong to cart business", 404)

        addon_snapshots: list[dict] = []
        modifiers = 0
        for addon_req in payload.addons:
            addon = await db.scalar(
                select(Addon).where(
                    Addon.id == addon_req.addon_id,
                    Addon.business_id == cart.business_id,
                    Addon.tenant_id == tenant_id,
                    Addon.is_active.is_(True),
                )
            )
            if not addon:
                raise AppError("ADDON_NOT_FOUND", "Addon not found", 404)
            if addon_req.quantity > addon.max_qty:
                raise AppError("ADDON_QTY_EXCEEDED", "Addon quantity exceeds max", 400)
            line_mod = addon.price_paise * addon_req.quantity
            modifiers += line_mod
            addon_snapshots.append(
                {
                    "addon_id": str(addon.id),
                    "name": addon.name,
                    "quantity": addon_req.quantity,
                    "unit_price_paise": addon.price_paise,
                    "line_paise": line_mod,
                }
            )

        item = CartItem(
            cart_id=cart.id,
            variant_id=variant.id,
            bundle_id=None,
            name_snapshot=f"{product.name} — {variant.name}",
            quantity=payload.quantity,
            addons=addon_snapshots,
            unit_price_paise=variant.base_price_paise,
            modifiers_paise=modifiers,
            metadata_json={},
        )
    else:
        bundle = await db.scalar(
            select(Bundle).where(
                Bundle.id == payload.bundle_id,
                Bundle.business_id == cart.business_id,
                Bundle.tenant_id == tenant_id,
                Bundle.is_active.is_(True),
            )
        )
        if not bundle:
            raise AppError("BUNDLE_NOT_FOUND", "Bundle not found", 404)
        if bundle.price_paise is None:
            raise AppError("BUNDLE_PRICE_MISSING", "Bundle has no fixed price", 400)
        item = CartItem(
            cart_id=cart.id,
            variant_id=None,
            bundle_id=bundle.id,
            name_snapshot=bundle.name,
            quantity=payload.quantity,
            addons=[],
            unit_price_paise=bundle.price_paise,
            modifiers_paise=0,
            metadata_json={"items": bundle.items},
        )

    db.add(item)
    await db.commit()
    cart = await _recalculate(db, cart)
    items = await _load_items(db, cart.id)
    return cart, items


async def update_item(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    cart_id: uuid.UUID,
    item_id: uuid.UUID,
    payload: CartItemUpdate,
) -> tuple[Cart, list[CartItem]]:
    cart, _ = await get_cart(db, tenant_id=tenant_id, cart_id=cart_id)
    item = await db.scalar(
        select(CartItem).where(CartItem.id == item_id, CartItem.cart_id == cart.id)
    )
    if not item:
        raise AppError("CART_ITEM_NOT_FOUND", "Cart item not found", 404)
    item.quantity = payload.quantity
    await db.commit()
    cart = await _recalculate(db, cart)
    return cart, await _load_items(db, cart.id)


async def remove_item(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    cart_id: uuid.UUID,
    item_id: uuid.UUID,
) -> tuple[Cart, list[CartItem]]:
    cart, _ = await get_cart(db, tenant_id=tenant_id, cart_id=cart_id)
    item = await db.scalar(
        select(CartItem).where(CartItem.id == item_id, CartItem.cart_id == cart.id)
    )
    if not item:
        raise AppError("CART_ITEM_NOT_FOUND", "Cart item not found", 404)
    await db.delete(item)
    await db.commit()
    cart = await _recalculate(db, cart)
    return cart, await _load_items(db, cart.id)


async def update_fees(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    cart_id: uuid.UUID,
    payload: CartFeesUpdate,
) -> tuple[Cart, list[CartItem]]:
    cart, _ = await get_cart(db, tenant_id=tenant_id, cart_id=cart_id)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(cart, key, value)
    await db.commit()
    cart = await _recalculate(db, cart)
    return cart, await _load_items(db, cart.id)
