"""Cart API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.pricing.schemas import PriceBreakdown


class CartAddonItem(BaseModel):
    addon_id: uuid.UUID
    quantity: int = Field(default=1, ge=1)


class CartItemCreate(BaseModel):
    variant_id: uuid.UUID | None = None
    bundle_id: uuid.UUID | None = None
    quantity: int = Field(default=1, ge=1)
    addons: list[CartAddonItem] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_target(self) -> CartItemCreate:
        if self.meta.get("line_type") == "COURIER_QUOTE":
            if "quoted_paise" not in self.meta:
                raise ValueError("quoted_paise required for courier quote line")
            return self
        if self.variant_id is None and self.bundle_id is None:
            raise ValueError("variant_id or bundle_id is required")
        if self.variant_id is not None and self.bundle_id is not None:
            raise ValueError("Provide only one of variant_id or bundle_id")
        return self


class CartItemUpdate(BaseModel):
    quantity: int | None = Field(default=None, ge=1)
    addons: list[CartAddonItem] | None = None
    meta: dict[str, Any] | None = None


class CartItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    cart_id: uuid.UUID
    variant_id: uuid.UUID | None
    bundle_id: uuid.UUID | None
    quantity: int
    addons: list[Any]
    unit_price_paise: int
    meta: dict[str, Any]


class CartCreate(BaseModel):
    business_id: uuid.UUID
    location_id: uuid.UUID | None = None
    currency: str = "INR"


class CartRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    business_id: uuid.UUID | None
    location_id: uuid.UUID | None
    currency: str
    pricing_snapshot: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    items: list[CartItemRead] = Field(default_factory=list)


class CartWithPricing(CartRead):
    pricing: PriceBreakdown | None = None
