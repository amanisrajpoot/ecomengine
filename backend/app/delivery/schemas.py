"""Delivery API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DeliveryStopCreate(BaseModel):
    sequence: int = Field(ge=0)
    stop_type: str
    address: dict[str, Any]
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    contact: dict[str, Any] = Field(default_factory=dict)


class DeliveryCreate(BaseModel):
    stops: list[DeliveryStopCreate] = Field(min_length=1)
    auto_assign: bool = True


class DeliveryStopRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    delivery_id: uuid.UUID
    sequence: int
    stop_type: str
    address: dict[str, Any]
    lat: float
    lng: float
    contact: dict[str, Any]
    status: str
    proof: dict[str, Any] | None
    completed_at: datetime | None


class DeliveryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    fulfillment_id: uuid.UUID
    partner_id: uuid.UUID | None
    vehicle_id: uuid.UUID | None
    status: str
    eta: datetime | None
    created_at: datetime
    updated_at: datetime
    stops: list[DeliveryStopRead] = Field(default_factory=list)


class StopComplete(BaseModel):
    proof: dict[str, Any] | None = None


class DeliveryAssign(BaseModel):
    partner_id: uuid.UUID
    vehicle_id: uuid.UUID | None = None


class TrackingStopRead(BaseModel):
    id: uuid.UUID
    sequence: int
    stop_type: str
    lat: float
    lng: float
    status: str


class TrackingRiderRead(BaseModel):
    partner_id: uuid.UUID
    lat: float
    lng: float
    updated_at: datetime
    is_online: bool


class OrderTrackingRead(BaseModel):
    order_id: uuid.UUID
    order_status: str
    delivery_id: uuid.UUID | None = None
    delivery_status: str | None = None
    eta: datetime | None = None
    rider: TrackingRiderRead | None = None
    stops: list[TrackingStopRead] = Field(default_factory=list)
