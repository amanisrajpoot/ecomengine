"""Ledger API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LedgerEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    order_id: uuid.UUID | None
    event_group_id: uuid.UUID
    event_type: str
    account: str
    direction: str
    amount_paise: int = Field(ge=1)
    currency: str
    metadata: dict[str, Any] = Field(validation_alias="meta")
    created_at: datetime


class LedgerPostingGroup(BaseModel):
    event_group_id: uuid.UUID
    event_type: str
    order_id: uuid.UUID | None
    entries: list[LedgerEntryRead]
