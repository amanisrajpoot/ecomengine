"""Pricing pipeline — computes full price breakdowns."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.businesses.service import get_business
from app.catalog.models import Addon, Bundle, Variant
from app.catalog.service import get_product
from app.core.errors import AppError
from app.taxation.service import calculate_checkout_tax
from app.pricing.schemas import CourierQuoteRequest, PriceBreakdown, PriceLine
from app.pricing.courier import quote_courier_fare_paise
from app.tenants.models import Tenant


async def calculate_cart_breakdown(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    items: list[Any],
    location_id: uuid.UUID | None = None,
) -> PriceBreakdown:
    business = await get_business(db, tenant_id=tenant_id, business_id=business_id)
    tenant = await db.get(Tenant, tenant_id)
    tenant_config = tenant.config if tenant else {}

    lines: list[PriceLine] = []
    subtotal_paise = 0

    for row in items:
        quantity = row.quantity
        meta = row.meta if isinstance(row.meta, dict) else {}
        if meta.get("line_type") == "COURIER_QUOTE":
            unit_price_paise = int(meta.get("quoted_paise", row.unit_price_paise or 0))
            line_total = unit_price_paise * quantity
            subtotal_paise += line_total
            lines.append(
                PriceLine(
                    cart_item_id=str(row.id) if hasattr(row, "id") else None,
                    name="Courier package",
                    quantity=quantity,
                    unit_price_paise=unit_price_paise,
                    line_total_paise=line_total,
                )
            )
            continue

        addons_json = row.addons or []
        unit_price_paise = 0
        name = "Item"
        variant_id_str: str | None = None
        bundle_id_str: str | None = None

        if row.variant_id is not None:
            variant = await db.scalar(
                select(Variant).where(
                    Variant.id == row.variant_id,
                    Variant.tenant_id == tenant_id,
                )
            )
            if not variant:
                raise AppError("VARIANT_NOT_FOUND", "Variant not found", status_code=404)
            product = await get_product(
                db,
                tenant_id=tenant_id,
                business_id=business_id,
                product_id=variant.product_id,
            )
            name = f"{product.name} ({variant.name})"
            variant_id_str = str(variant.id)
            unit_price_paise = variant.base_price_paise

            addon_total = 0
            resolved_addons: list[dict[str, Any]] = []
            for addon_row in addons_json:
                addon_id = addon_row.get("addon_id")
                addon_qty = int(addon_row.get("quantity", 1))
                if not addon_id:
                    continue
                addon_uuid = uuid.UUID(str(addon_id))
                addon = await db.scalar(
                    select(Addon).where(
                        Addon.id == addon_uuid,
                        Addon.business_id == business_id,
                        Addon.tenant_id == tenant_id,
                    )
                )
                if not addon:
                    raise AppError("ADDON_NOT_FOUND", "Addon not found", status_code=404)
                addon_price = addon.price_paise * addon_qty
                addon_total += addon_price
                resolved_addons.append(
                    {
                        "addon_id": str(addon.id),
                        "name": addon.name,
                        "quantity": addon_qty,
                        "price_paise": addon.price_paise,
                    }
                )
            unit_price_paise += addon_total
            line_total = unit_price_paise * quantity
            subtotal_paise += line_total
            lines.append(
                PriceLine(
                    cart_item_id=str(row.id) if hasattr(row, "id") else None,
                    variant_id=variant_id_str,
                    name=name,
                    quantity=quantity,
                    unit_price_paise=unit_price_paise,
                    line_total_paise=line_total,
                    addons=resolved_addons,
                )
            )
        elif row.bundle_id is not None:
            bundle = await db.scalar(
                select(Bundle).where(
                    Bundle.id == row.bundle_id,
                    Bundle.business_id == business_id,
                    Bundle.tenant_id == tenant_id,
                )
            )
            if not bundle:
                raise AppError("BUNDLE_NOT_FOUND", "Bundle not found", status_code=404)
            name = bundle.name
            bundle_id_str = str(bundle.id)
            if bundle.price_paise is not None:
                unit_price_paise = bundle.price_paise
            else:
                unit_price_paise = 0
                for bundle_item in bundle.items:
                    v_id = bundle_item.get("variant_id")
                    if not v_id:
                        continue
                    variant = await db.scalar(
                        select(Variant).where(
                            Variant.id == uuid.UUID(str(v_id)),
                            Variant.tenant_id == tenant_id,
                        )
                    )
                    if variant:
                        qty = int(bundle_item.get("quantity", 1))
                        unit_price_paise += variant.base_price_paise * qty
            line_total = unit_price_paise * quantity
            subtotal_paise += line_total
            lines.append(
                PriceLine(
                    cart_item_id=str(row.id) if hasattr(row, "id") else None,
                    bundle_id=bundle_id_str,
                    name=name,
                    quantity=quantity,
                    unit_price_paise=unit_price_paise,
                    line_total_paise=line_total,
                )
            )
        else:
            raise AppError("INVALID_CART_ITEM", "Cart item must have variant_id or bundle_id", 400)

    _ = location_id

    delivery_fee_paise = 0
    if business.type != "COURIER" and business.capabilities.get("delivery", False):
        settings_extra = business.settings.get("extra", {}) if isinstance(business.settings, dict) else {}
        delivery_fee_paise = int(settings_extra.get("delivery_fee_paise", 3000))

    platform_fee_paise = int(tenant_config.get("platform_fee_paise", 500))
    discount_paise = 0
    other_fees_paise = 0

    taxable_base = subtotal_paise - discount_paise + delivery_fee_paise + platform_fee_paise
    tax_paise, tax_lines = await calculate_checkout_tax(
        db,
        tenant_id=tenant_id,
        goods_taxable_paise=subtotal_paise - discount_paise,
        delivery_taxable_paise=delivery_fee_paise,
        platform_fee_paise=0,
    )

    total_paise = (
        subtotal_paise
        - discount_paise
        + delivery_fee_paise
        + platform_fee_paise
        + other_fees_paise
        + tax_paise
    )

    return PriceBreakdown(
        subtotal_paise=subtotal_paise,
        discount_paise=discount_paise,
        delivery_fee_paise=delivery_fee_paise,
        platform_fee_paise=platform_fee_paise,
        other_fees_paise=other_fees_paise,
        tax_paise=tax_paise,
        tax_lines=tax_lines,
        total_paise=total_paise,
        lines=lines,
    )


async def quote_courier_delivery(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    payload: CourierQuoteRequest,
) -> tuple[PriceBreakdown, dict]:
    business = await get_business(
        db, tenant_id=tenant_id, business_id=payload.business_id
    )
    if business.type != "COURIER":
        raise AppError(
            "NOT_COURIER_BUSINESS",
            "Courier quotes require a COURIER business",
            status_code=400,
        )

    tenant = await db.get(Tenant, tenant_id)
    tenant_config = tenant.config if tenant else {}

    try:
        fare_paise, distance_km, fare_details = quote_courier_fare_paise(
            pickup_lat=payload.pickup.lat,
            pickup_lng=payload.pickup.lng,
            drop_lat=payload.drop.lat,
            drop_lng=payload.drop.lng,
            weight_kg=payload.weight_kg,
            vehicle_type=payload.vehicle_type,
            express=payload.express,
            tenant_config=tenant_config,
        )
    except ValueError as exc:
        raise AppError("INVALID_COURIER_QUOTE", str(exc), status_code=400) from exc

    platform_fee_paise = int(tenant_config.get("platform_fee_paise", 500))
    discount_paise = 0
    delivery_fee_paise = 0
    other_fees_paise = 0

    tax_paise, tax_lines = await calculate_checkout_tax(
        db,
        tenant_id=tenant_id,
        goods_taxable_paise=fare_paise,
        delivery_taxable_paise=0,
        platform_fee_paise=0,
    )

    total_paise = fare_paise + platform_fee_paise + tax_paise

    breakdown = PriceBreakdown(
        subtotal_paise=fare_paise,
        discount_paise=discount_paise,
        delivery_fee_paise=delivery_fee_paise,
        platform_fee_paise=platform_fee_paise,
        other_fees_paise=other_fees_paise,
        tax_paise=tax_paise,
        tax_lines=tax_lines,
        total_paise=total_paise,
        lines=[
            PriceLine(
                name="Courier package",
                quantity=1,
                unit_price_paise=fare_paise,
                line_total_paise=fare_paise,
            )
        ],
    )

    quote = {
        "line_type": "COURIER_QUOTE",
        "quoted_paise": fare_paise,
        "pickup": payload.pickup.model_dump(),
        "drop": payload.drop.model_dump(),
        "weight_kg": payload.weight_kg,
        "vehicle_type": payload.vehicle_type.upper(),
        "express": payload.express,
        "distance_km": distance_km,
        "fare_details": fare_details,
    }
    return breakdown, quote
