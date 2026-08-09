"""Fulfillment API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FulfillmentCreateBody(BaseModel):
    type: str | None = Field(
        default=None,
        pattern=r"^(DELIVERY|PICKUP|SELF_PICKUP|SCHEDULED|MULTI_STOP)$",
    )
    scheduled_for: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class FulfillmentTransitionRequest(BaseModel):
    to_status: str = Field(min_length=1, max_length=64)
    actor: str = Field(
        default="system",
        pattern=r"^(system|customer|merchant|staff|rider)$",
    )
    reason: str | None = None


class FulfillmentStatusEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    fulfillment_id: uuid.UUID
    from_status: str | None
    to_status: str
    actor_user_id: uuid.UUID | None
    actor_role: str | None
    reason: str | None
    created_at: datetime


class FulfillmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    order_id: uuid.UUID
    type: str
    status: str
    scheduled_for: datetime | None
    metadata: dict[str, Any] = Field(validation_alias="metadata_json")
    created_at: datetime
    updated_at: datetime
    status_events: list[FulfillmentStatusEventRead] = Field(default_factory=list)
