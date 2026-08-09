"""Delivery API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StopCreate(BaseModel):
    sequence: int = Field(ge=0)
    stop_type: str = Field(pattern=r"^(PICKUP|DROP)$")
    address: dict[str, Any] = Field(default_factory=dict)
    lat: float | None = None
    lng: float | None = None
    contact: dict[str, Any] = Field(default_factory=dict)


class DeliveryCreateBody(BaseModel):
    stops: list[StopCreate] = Field(default_factory=list)
    eta: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    # When empty, system builds default pickup/drop from location + metadata.
    auto_stops: bool = True


class AssignDeliveryBody(BaseModel):
    partner_id: uuid.UUID | None = None  # None = run V1 auto-assignment
    vehicle_id: uuid.UUID | None = None
    auto_accept: bool = True


class DeliveryTransitionBody(BaseModel):
    to_status: str = Field(min_length=1, max_length=32)
    reason: str | None = None


class TrackingUpdateBody(BaseModel):
    lat: float
    lng: float
    heading: float | None = None
    speed_kmh: float | None = None


class CompleteStopBody(BaseModel):
    proof: dict[str, Any] = Field(default_factory=dict)
    # e.g. {"otp": "1234", "photo_url": "...", "signature": "..."}


class DeliveryStopRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    delivery_id: uuid.UUID
    sequence: int
    stop_type: str
    address: dict[str, Any]
    lat: float | None
    lng: float | None
    contact: dict[str, Any]
    status: str
    proof: dict[str, Any] | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class DeliveryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    fulfillment_id: uuid.UUID
    partner_id: uuid.UUID | None
    vehicle_id: uuid.UUID | None
    status: str
    eta: datetime | None
    metadata: dict[str, Any] = Field(validation_alias="metadata_json")
    created_at: datetime
    updated_at: datetime
    stops: list[DeliveryStopRead] = Field(default_factory=list)
