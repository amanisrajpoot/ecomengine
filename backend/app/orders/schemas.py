"""Order API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CheckoutRequest(BaseModel):
    cart_id: uuid.UUID
    payment_method: str = Field(default="ONLINE", pattern=r"^(ONLINE|COD)$")
    fulfillment_type: str = Field(default="DELIVERY", pattern=r"^(DELIVERY|PICKUP|SELF_PICKUP)$")
    # Optional override; normally derived from business type.
    state_machine_profile: str | None = None


class OrderTransitionRequest(BaseModel):
    to_status: str = Field(min_length=1, max_length=64)
    actor: str = Field(
        default="system",
        pattern=r"^(system|customer|merchant|staff|rider|payments)$",
    )
    reason: str | None = None


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_id: uuid.UUID
    variant_id: uuid.UUID | None
    bundle_id: uuid.UUID | None
    name_snapshot: str
    quantity: int
    unit_price_paise: int
    modifiers_paise: int
    addons_snapshot: list[Any]
    metadata: dict[str, Any] = Field(validation_alias="metadata_json")


class OrderStatusEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_id: uuid.UUID
    from_status: str | None
    to_status: str
    actor_user_id: uuid.UUID | None
    actor_role: str | None
    reason: str | None
    created_at: datetime


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    business_id: uuid.UUID | None
    location_id: uuid.UUID | None
    cart_id: uuid.UUID | None
    status: str
    state_machine_profile: str
    currency: str
    pricing_snapshot: dict[str, Any]
    fulfillment_type: str
    payment_method: str
    placed_at: datetime | None
    metadata: dict[str, Any] = Field(validation_alias="metadata_json")
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemRead] = []
    status_events: list[OrderStatusEventRead] = []
