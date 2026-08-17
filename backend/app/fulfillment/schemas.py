"""Fulfillment API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FulfillmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    order_id: uuid.UUID
    type: str
    status: str
    scheduled_for: datetime | None
    metadata: dict[str, Any] = Field(validation_alias="meta")
    created_at: datetime
    updated_at: datetime


class FulfillmentTransition(BaseModel):
    to_status: str = Field(min_length=1, max_length=32)
    reason: str | None = None
    scheduled_for: datetime | None = None
