"""Map core domain entities to ONDC catalog / order shapes."""

from __future__ import annotations

from typing import Any

from app.businesses.models import Business
from app.catalog.models import Product, Variant
from app.orders.models import Order
from app.pricing.schemas import PriceBreakdown

from app.integrations.ondc.schemas import OndcItem, OndcProvider, OndcQuote


def business_to_provider(business: Business) -> OndcProvider:
    return OndcProvider(
        id=str(business.id),
        name=business.name,
        type=business.type,
        descriptor={
            "short_desc": business.description or "",
            "status": business.status,
        },
    )


def variant_to_item(product: Product, variant: Variant) -> OndcItem:
    return OndcItem(
        id=str(variant.id),
        provider_id=str(product.business_id),
        product_id=str(product.id),
        name=f"{product.name} — {variant.name}",
        price_paise=variant.base_price_paise,
        currency="INR",
    )


def breakdown_to_quote(cart_id, breakdown: PriceBreakdown) -> OndcQuote:
    return OndcQuote(
        cart_id=cart_id,
        currency=breakdown.currency,
        total_paise=breakdown.total_paise,
        subtotal_paise=breakdown.subtotal_paise,
        tax_paise=breakdown.tax_paise,
    )


def order_to_status_payload(order: Order) -> dict[str, Any]:
    return {
        "order_id": str(order.id),
        "state": order.status,
        "profile": order.state_machine_profile,
        "fulfillment_type": order.fulfillment_type,
        "placed_at": order.placed_at.isoformat() if order.placed_at else None,
        "pricing_snapshot": order.pricing_snapshot,
    }
