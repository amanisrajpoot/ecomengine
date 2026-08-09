"""Cart API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CartCreate(BaseModel):
    business_id: uuid.UUID
    location_id: uuid.UUID | None = None
    delivery_fee_paise: int = Field(ge=0, default=3000)
    platform_fee_paise: int = Field(ge=0, default=500)
    discount_paise: int = Field(ge=0, default=0)


class CartItemAddon(BaseModel):
    addon_id: uuid.UUID
    quantity: int = Field(ge=1, default=1)


class CartItemCreate(BaseModel):
    variant_id: uuid.UUID | None = None
    bundle_id: uuid.UUID | None = None
    quantity: int = Field(ge=1, default=1)
    addons: list[CartItemAddon] = Field(default_factory=list)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1)


class CartFeesUpdate(BaseModel):
    delivery_fee_paise: int | None = Field(default=None, ge=0)
    platform_fee_paise: int | None = Field(default=None, ge=0)
    discount_paise: int | None = Field(default=None, ge=0)


class CartItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    cart_id: uuid.UUID
    variant_id: uuid.UUID | None
    bundle_id: uuid.UUID | None
    name_snapshot: str
    quantity: int
    addons: list[Any]
    unit_price_paise: int
    modifiers_paise: int
    metadata: dict[str, Any] = Field(validation_alias="metadata_json")


class CartRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    business_id: uuid.UUID | None
    location_id: uuid.UUID | None
    currency: str
    pricing_snapshot: dict[str, Any]
    discount_paise: int
    delivery_fee_paise: int
    platform_fee_paise: int
    status: str
    created_at: datetime
    updated_at: datetime
    items: list[CartItemRead] = []
