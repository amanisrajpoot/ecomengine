"""Courier quote + shipment schemas (no CourierOrder model)."""

from __future__ import annotations

import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.pricing.schemas import PriceBreakdown


class GeoPoint(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    address: dict[str, Any] = Field(default_factory=dict)
    contact: dict[str, Any] = Field(default_factory=dict)


class CourierQuoteRequest(BaseModel):
    pickup: GeoPoint
    drop: GeoPoint
    weight_kg: float = Field(gt=0, le=200)
    vehicle_type: Literal["BIKE", "SCOOTER", "CAR", "VAN"] = "BIKE"
    express: bool = False
    platform_fee_paise: int = Field(ge=0, default=500)
    business_id: uuid.UUID | None = None


class CourierQuoteRead(BaseModel):
    distance_km: float
    weight_kg: float
    vehicle_type: str
    express: bool
    fare_components: dict[str, int]
    pricing: PriceBreakdown


class CourierShipmentCreate(BaseModel):
    business_id: uuid.UUID
    pickup: GeoPoint
    drop: GeoPoint
    weight_kg: float = Field(gt=0, le=200)
    vehicle_type: Literal["BIKE", "SCOOTER", "CAR", "VAN"] = "BIKE"
    express: bool = False
    package_notes: str | None = None
    payment_provider: str = Field(default="cod", min_length=2, max_length=32)
    customer_phone: str | None = None
    customer_email: str | None = None
    return_url: str | None = None
    notify_url: str | None = None
    platform_fee_paise: int = Field(ge=0, default=500)
