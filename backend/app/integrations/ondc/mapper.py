"""Map internal catalog/orders to Beckn catalog and order shapes."""

from __future__ import annotations

import uuid
from typing import Any

from app.catalog.models import Product, Variant
from app.locations.schemas import NearbyStoreRead
from app.orders.models import Order, OrderItem

OFFER_PREFIX = "ce"


def offer_id(*, business_id: uuid.UUID, location_id: uuid.UUID, variant_id: uuid.UUID) -> str:
    return f"{OFFER_PREFIX}:{business_id}:{location_id}:{variant_id}"


def parse_offer_id(offer: str) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID]:
    parts = offer.split(":")
    if len(parts) != 4 or parts[0] != OFFER_PREFIX:
        raise ValueError(f"Invalid offer id: {offer}")
    return uuid.UUID(parts[1]), uuid.UUID(parts[2]), uuid.UUID(parts[3])


def provider_id(business_id: uuid.UUID, location_id: uuid.UUID) -> str:
    return f"{OFFER_PREFIX}-provider:{business_id}:{location_id}"


def parse_provider_id(provider: str) -> tuple[uuid.UUID, uuid.UUID]:
    if not provider.startswith(f"{OFFER_PREFIX}-provider:"):
        raise ValueError(f"Invalid provider id: {provider}")
    _, business_id, location_id = provider.split(":", 2)
    return uuid.UUID(business_id), uuid.UUID(location_id)


def _item_descriptor(
    *,
    product: Product,
    variant: Variant,
    business_id: uuid.UUID,
    location_id: uuid.UUID,
) -> dict[str, Any]:
    oid = offer_id(business_id=business_id, location_id=location_id, variant_id=variant.id)
    return {
        "id": oid,
        "descriptor": {"name": f"{product.name} — {variant.name}"},
        "price": {
            "currency": "INR",
            "value": f"{variant.base_price_paise / 100:.2f}",
        },
        "quantity": {"available": {"count": "99"}, "maximum": {"count": "10"}},
        "@ondc/org/item_id": str(variant.id),
    }


def build_catalog(
    stores: list[NearbyStoreRead],
    *,
    catalog_by_business: dict[uuid.UUID, list[tuple[Product, list[Variant]]]],
) -> dict[str, Any]:
    providers: list[dict[str, Any]] = []
    for store in stores:
        pid = provider_id(store.business_id, store.location_id)
        items: list[dict[str, Any]] = []
        for product, variants in catalog_by_business.get(store.business_id, []):
            for variant in variants:
                if not variant.is_available:
                    continue
                items.append(
                    _item_descriptor(
                        product=product,
                        variant=variant,
                        business_id=store.business_id,
                        location_id=store.location_id,
                    )
                )
        if not items:
            continue
        providers.append(
            {
                "id": pid,
                "descriptor": {"name": store.business_name, "short_desc": store.location_name},
                "locations": [
                    {
                        "id": str(store.location_id),
                        "gps": f"{store.lat},{store.lng}",
                        "address": store.address,
                    }
                ],
                "items": items,
            }
        )
    return {"catalog": {"bpp/providers": providers}}


def build_order_quote(
    *,
    order: Order,
    items: list[OrderItem],
    provider: str,
) -> dict[str, Any]:
    total = order.pricing_snapshot.get("total_paise", 0)
    return {
        "order": {
            "provider": {"id": provider},
            "items": [
                {
                    "id": item.metadata_json.get("ondc_offer_id", str(item.variant_id)),
                    "quantity": {"count": item.quantity},
                    "price": {
                        "currency": "INR",
                        "value": f"{(item.unit_price_paise + item.modifiers_paise) * item.quantity / 100:.2f}",
                    },
                }
                for item in items
            ],
            "billing": {"phone": order.metadata_json.get("ondc_customer_phone")},
            "payment": {"type": "ON-ORDER", "@ondc/org/settlement_details": []},
            "quote": {
                "price": {"currency": "INR", "value": f"{total / 100:.2f}"},
                "breakup": [
                    {
                        "title": "base_price",
                        "price": {"currency": "INR", "value": f"{total / 100:.2f}"},
                    }
                ],
            },
        }
    }


def map_order_state(status: str) -> str:
    if status == "CANCELLED":
        return "Cancelled"
    if status == "DELIVERED":
        return "Completed"
    if status in {"PAYMENT_CONFIRMED"}:
        return "Created"
    return "In-progress"
