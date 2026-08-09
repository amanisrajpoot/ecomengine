"""Courier fare quote — base + distance + weight + vehicle (+ optional express)."""

from __future__ import annotations

from app.courier.schemas import CourierQuoteRead, CourierQuoteRequest, GeoPoint
from app.delivery.geo import haversine_km
from app.pricing.engine import price_items
from app.pricing.schemas import PricingContext, PricingInputItem

# Simple India-first V1 tariff (paise). Tunable later via business settings.
BASE_FARE_PAISE = 3000
PER_KM_PAISE = 1200
PER_KG_PAISE = 500
EXPRESS_SURCHARGE_PAISE = 2500

VEHICLE_MULTIPLIER: dict[str, float] = {
    "BIKE": 1.0,
    "SCOOTER": 1.05,
    "CAR": 1.4,
    "VAN": 1.8,
}


def quote_fare(payload: CourierQuoteRequest, *, tax_rules: list | None = None) -> CourierQuoteRead:
    distance_km = haversine_km(
        payload.pickup.lat,
        payload.pickup.lng,
        payload.drop.lat,
        payload.drop.lng,
    )
    # Bill at least 1 km so tiny hops still cover dispatch cost.
    billable_km = max(distance_km, 1.0)
    base = BASE_FARE_PAISE
    distance_component = int(round(billable_km * PER_KM_PAISE))
    weight_component = int(round(payload.weight_kg * PER_KG_PAISE))
    subtotal = base + distance_component + weight_component
    mult = VEHICLE_MULTIPLIER.get(payload.vehicle_type, 1.0)
    vehicle_adjusted = int(round(subtotal * mult))
    vehicle_premium = vehicle_adjusted - subtotal
    express = EXPRESS_SURCHARGE_PAISE if payload.express else 0
    fare_paise = vehicle_adjusted + express

    components = {
        "base_fare_paise": base,
        "distance_paise": distance_component,
        "weight_paise": weight_component,
        "vehicle_premium_paise": vehicle_premium,
        "express_surcharge_paise": express,
        "fare_paise": fare_paise,
    }

    pricing = price_items(
        [
            PricingInputItem(
                name=f"Courier {payload.vehicle_type} · {billable_km:.1f}km · {payload.weight_kg:g}kg",
                quantity=1,
                unit_price_paise=fare_paise,
            )
        ],
        PricingContext(
            currency="INR",
            delivery_fee_paise=0,
            platform_fee_paise=payload.platform_fee_paise,
            other_fees_paise=0,
            tax_rate_bps=500,
            tax_jurisdiction="IN-INTRA",
        ),
        tax_rules=tax_rules,
    )
    return CourierQuoteRead(
        distance_km=round(distance_km, 3),
        weight_kg=payload.weight_kg,
        vehicle_type=payload.vehicle_type,
        express=payload.express,
        fare_components=components,
        pricing=pricing,
    )


def point_dict(point: GeoPoint) -> dict:
    return {
        "lat": point.lat,
        "lng": point.lng,
        "address": point.address or {},
        "contact": point.contact or {},
    }
