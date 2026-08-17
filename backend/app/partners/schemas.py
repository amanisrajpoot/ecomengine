"""Partner API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PartnerProfileCreate(BaseModel):
    documents: dict[str, Any] = Field(default_factory=dict)
    service_area: dict[str, Any] | None = None


class PartnerProfileUpdate(BaseModel):
    status: str | None = None
    is_online: bool | None = None
    documents: dict[str, Any] | None = None
    current_lat: float | None = Field(default=None, ge=-90, le=90)
    current_lng: float | None = Field(default=None, ge=-180, le=180)
    service_area: dict[str, Any] | None = None


class PartnerLocationUpdate(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class PartnerProfileRead(BaseModel):
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
    created_at: datetime
    updated_at: datetime


class VehicleCreate(BaseModel):
    vehicle_type: str = Field(min_length=1, max_length=32)
    registration: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class VehicleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    partner_id: uuid.UUID
    vehicle_type: str
    registration: str | None
    metadata: dict[str, Any] = Field(validation_alias="meta")
    created_at: datetime
    updated_at: datetime
