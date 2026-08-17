"""Location API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Address(BaseModel):
    line1: str = Field(min_length=1, max_length=200)
    line2: str | None = None
    landmark: str | None = None
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    pincode: str = Field(min_length=4, max_length=12)
    country: str = "IN"


class DayHours(BaseModel):
    day: str = Field(pattern=r"^(MON|TUE|WED|THU|FRI|SAT|SUN)$")
    open: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    close: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    closed: bool = False


class LocationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    address: Address
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    hours: list[DayHours] = Field(default_factory=list)
    timezone: str = "Asia/Kolkata"
    is_active: bool = True
    service_area: dict[str, Any] | None = None


class LocationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    address: Address | None = None
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    hours: list[DayHours] | None = None
    timezone: str | None = None
    is_active: bool | None = None
    service_area: dict[str, Any] | None = None


class LocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    business_id: uuid.UUID
    name: str
    address: dict[str, Any]
    lat: float
    lng: float
    service_area: dict[str, Any] | None
    hours: list[dict[str, Any]]
    timezone: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
