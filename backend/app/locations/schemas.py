"""Location schemas (India address + geo + hours)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class IndiaAddress(BaseModel):
    line1: str = Field(min_length=1, max_length=200)
    line2: str | None = None
    landmark: str | None = None
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    pincode: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
    country: str = "IN"


class ServiceAreaRadius(BaseModel):
    type: str = "radius"
    radius_km: float = Field(gt=0, le=100)


class ServiceAreaPolygon(BaseModel):
    type: str = "polygon"
    # List of [lng, lat] rings (GeoJSON-ish); validated lightly in Phase 2.
    coordinates: list[list[list[float]]]


class DayHours(BaseModel):
    day: str  # mon..sun
    open: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    close: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    closed: bool = False


class BusinessLocationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    address: IndiaAddress
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    service_area: dict[str, Any] | None = None
    hours: list[DayHours] = Field(default_factory=list)
    timezone: str = "Asia/Kolkata"
    is_active: bool = True

    @field_validator("hours")
    @classmethod
    def validate_hours(cls, value: list[DayHours]) -> list[DayHours]:
        days = {h.day.lower() for h in value}
        allowed = {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}
        if days - allowed:
            raise ValueError("hours.day must be mon..sun")
        return value


class BusinessLocationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    address: IndiaAddress | None = None
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    service_area: dict[str, Any] | None = None
    hours: list[DayHours] | None = None
    timezone: str | None = None
    is_active: bool | None = None


class BusinessLocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    business_id: uuid.UUID
    name: str
    address: dict[str, Any]
    lat: float
    lng: float
    service_area: dict[str, Any] | None
    hours: list[Any] | dict[str, Any]
    timezone: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
