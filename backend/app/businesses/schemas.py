"""Business configuration and API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.identity.rbac import Role


class BusinessType(StrEnum):
    FOOD = "FOOD"
    RETAIL = "RETAIL"
    GROCERY = "GROCERY"
    COURIER = "COURIER"


class BusinessStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"


class BusinessContact(BaseModel):
    phone: str | None = None
    email: str | None = None
    whatsapp: str | None = None


class BusinessConfig(BaseModel):
    preparation_time_minutes: int | None = None
    accepts_scheduled_orders: bool = False
    currency: str = "INR"
    timezone: str = "Asia/Kolkata"
    extra: dict[str, Any] = Field(default_factory=dict)


class BusinessCapabilities(BaseModel):
    catalog: bool = True
    inventory: bool = False
    addons: bool = False
    delivery: bool = True
    scheduledOrders: bool = False


def default_capabilities(business_type: str | BusinessType) -> dict[str, bool]:
    presets: dict[str, dict[str, bool]] = {
        BusinessType.FOOD: {
            "catalog": True,
            "inventory": False,
            "addons": True,
            "delivery": True,
            "scheduledOrders": True,
        },
        BusinessType.GROCERY: {
            "catalog": True,
            "inventory": True,
            "addons": False,
            "delivery": True,
            "scheduledOrders": True,
        },
        BusinessType.RETAIL: {
            "catalog": True,
            "inventory": True,
            "addons": False,
            "delivery": True,
            "scheduledOrders": False,
        },
        BusinessType.COURIER: {
            "catalog": False,
            "inventory": False,
            "addons": False,
            "delivery": True,
            "scheduledOrders": True,
        },
    }
    key = business_type.value if isinstance(business_type, BusinessType) else business_type
    return presets.get(key, presets[BusinessType.FOOD]).copy()


class BusinessCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    type: BusinessType = BusinessType.FOOD
    description: str | None = None
    logo_url: str | None = None
    contact: BusinessContact = Field(default_factory=BusinessContact)
    settings: BusinessConfig = Field(default_factory=BusinessConfig)
    # Optional overrides merged onto type defaults.
    capabilities: BusinessCapabilities | None = None
    status: BusinessStatus = BusinessStatus.DRAFT


class BusinessUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    logo_url: str | None = None
    contact: BusinessContact | None = None
    settings: BusinessConfig | None = None
    capabilities: BusinessCapabilities | None = None
    status: BusinessStatus | None = None


class BusinessRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    type: str
    name: str
    description: str | None
    logo_url: str | None
    contact: dict[str, Any]
    settings: dict[str, Any]
    capabilities: dict[str, Any]
    status: str
    created_at: datetime
    updated_at: datetime


class StaffMemberRead(BaseModel):
    binding_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    email: str | None
    phone: str | None
    display_name: str | None
    created_at: datetime


class StaffAssign(BaseModel):
    user_id: uuid.UUID | None = None
    email: EmailStr | None = None
    phone: str | None = Field(default=None, min_length=8, max_length=20)
    role: Role = Role.STAFF

    @model_validator(mode="after")
    def _require_identifier(self) -> StaffAssign:
        if self.user_id is None and self.email is None and self.phone is None:
            raise ValueError("user_id, email, or phone is required")
        return self

    @model_validator(mode="after")
    def _role_allowed(self) -> StaffAssign:
        if self.role not in {Role.STAFF, Role.BUSINESS_MANAGER}:
            raise ValueError("role must be STAFF or BUSINESS_MANAGER")
        return self
