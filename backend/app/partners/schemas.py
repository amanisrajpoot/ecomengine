"""Partner / vehicle API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PartnerCreate(BaseModel):
    user_id: uuid.UUID
    display_name: str | None = None
    documents: dict[str, Any] = Field(default_factory=dict)
    service_area: dict[str, Any] | None = None
    status: str = Field(default="ACTIVE", pattern=r"^(ACTIVE|INACTIVE|SUSPENDED)$")


class PartnerUpdate(BaseModel):
    display_name: str | None = None
    status: str | None = Field(default=None, pattern=r"^(ACTIVE|INACTIVE|SUSPENDED)$")
    is_online: bool | None = None
    documents: dict[str, Any] | None = None
    service_area: dict[str, Any] | None = None
    current_lat: float | None = None
    current_lng: float | None = None


class PartnerLocationUpdate(BaseModel):
    lat: float
    lng: float
    is_online: bool | None = None


class PartnerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    status: str
    is_online: bool
    documents: dict[str, Any]
    current_lat: float | None
    current_lng: float | None
    service_area: dict[str, Any] | None
    display_name: str | None
    created_at: datetime
    updated_at: datetime


class VehicleCreate(BaseModel):
    partner_id: uuid.UUID
    vehicle_type: str = Field(default="BIKE", pattern=r"^(BIKE|SCOOTER|CAR|VAN|OTHER)$")
    registration: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class VehicleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    partner_id: uuid.UUID
    vehicle_type: str
    registration: str | None
    metadata: dict[str, Any] = Field(validation_alias="metadata_json")
    is_active: bool
    created_at: datetime
    updated_at: datetime
