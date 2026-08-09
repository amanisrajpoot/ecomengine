"""Notification API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: uuid.UUID | None
    order_id: uuid.UUID | None
    event_name: str
    channel: str
    recipient: str
    subject: str | None
    body: str
    status: str
    provider: str | None
    provider_ref: str | None
    metadata: dict[str, Any] = Field(validation_alias="metadata_json")
    created_at: datetime
