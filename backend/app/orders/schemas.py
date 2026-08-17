"""Order API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OrderCheckout(BaseModel):
    cart_id: uuid.UUID
    fulfillment_type: str = "DELIVERY"


class OrderTransition(BaseModel):
    to_status: str = Field(min_length=1, max_length=32)
    reason: str | None = None


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_id: uuid.UUID
    variant_id: uuid.UUID | None
    name_snapshot: str
    quantity: int
    unit_price_paise: int
    addons_snapshot: list[Any]
    meta: dict[str, Any]


class OrderStatusEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_id: uuid.UUID
    from_status: str | None
    to_status: str
    actor_user_id: uuid.UUID | None
    reason: str | None
    created_at: datetime


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    business_id: uuid.UUID | None
    location_id: uuid.UUID | None
    status: str
    state_machine_profile: str
    currency: str
    pricing_snapshot: dict[str, Any]
    fulfillment_type: str
    placed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemRead] = Field(default_factory=list)


class OrderDetail(OrderRead):
    status_events: list[OrderStatusEventRead] = Field(default_factory=list)
