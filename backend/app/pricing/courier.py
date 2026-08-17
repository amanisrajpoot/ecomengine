"""Courier fare quote helpers (distance, weight, vehicle)."""

from __future__ import annotations

import math

VEHICLE_SURCHARGE_PAISE: dict[str, int] = {
    "BIKE": 0,
    "CAR": 3000,
    "VAN": 5000,
}

DEFAULT_BASE_FARE_PAISE = 5000
DEFAULT_PER_KM_PAISE = 1500
DEFAULT_PER_KG_PAISE = 500
DEFAULT_EXPRESS_SURCHARGE_PAISE = 2000


def distance_km(
    pickup_lat: float,
    pickup_lng: float,
    drop_lat: float,
    drop_lng: float,
) -> float:
    radius = 6371.0
    phi1, phi2 = math.radians(pickup_lat), math.radians(drop_lat)
    dphi = math.radians(drop_lat - pickup_lat)
    dlambda = math.radians(drop_lng - pickup_lng)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def quote_courier_fare_paise(
    *,
    pickup_lat: float,
    pickup_lng: float,
    drop_lat: float,
    drop_lng: float,
    weight_kg: float,
    vehicle_type: str,
    express: bool = False,
    tenant_config: dict | None = None,
) -> tuple[int, float, dict]:
    config = tenant_config or {}
    courier_cfg = config.get("courier_pricing", {}) if isinstance(config, dict) else {}

    base_fare = int(courier_cfg.get("base_fare_paise", DEFAULT_BASE_FARE_PAISE))
    per_km = int(courier_cfg.get("per_km_paise", DEFAULT_PER_KM_PAISE))
    per_kg = int(courier_cfg.get("per_kg_paise", DEFAULT_PER_KG_PAISE))
    express_surcharge = int(
        courier_cfg.get("express_surcharge_paise", DEFAULT_EXPRESS_SURCHARGE_PAISE)
    )

    km = distance_km(pickup_lat, pickup_lng, drop_lat, drop_lng)
    vehicle_key = vehicle_type.upper()
    if vehicle_key not in VEHICLE_SURCHARGE_PAISE:
        raise ValueError(f"Unknown vehicle_type {vehicle_type}")

    vehicle_extra = VEHICLE_SURCHARGE_PAISE[vehicle_key]
    express_extra = express_surcharge if express else 0
    distance_component = int(round(km * per_km))
    weight_component = int(round(weight_kg * per_kg))
    fare = base_fare + distance_component + weight_component + vehicle_extra + express_extra

    details = {
        "base_fare_paise": base_fare,
        "distance_km": round(km, 3),
        "distance_component_paise": distance_component,
        "weight_kg": weight_kg,
        "weight_component_paise": weight_component,
        "vehicle_type": vehicle_key,
        "vehicle_surcharge_paise": vehicle_extra,
        "express_surcharge_paise": express_extra,
        "quoted_paise": fare,
    }
    return fare, km, details
