"""Tenant and platform config schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TenantConfig(BaseModel):
    """Tenant-level feature and policy knobs."""

    default_currency: str = "INR"
    default_timezone: str = "Asia/Kolkata"
    otp_enabled: bool = True
    password_auth_enabled: bool = True
    allow_self_serve_business: bool = False
    extra: dict[str, Any] = Field(default_factory=dict)


class TenantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    config: TenantConfig = Field(default_factory=TenantConfig)


class TenantUpdateConfig(BaseModel):
    config: TenantConfig


class TenantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    status: str
    config: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class PlatformConfigUpsert(BaseModel):
    value: dict[str, Any]


class PlatformConfigRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    key: str
    value: dict[str, Any]
    updated_at: datetime
