"""Settlement API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SettlementCalculate(BaseModel):
    party_type: str
    party_id: uuid.UUID
    period_start: datetime
    period_end: datetime
    currency: str = "INR"


class SettlementTransition(BaseModel):
    to_status: str
    reason: str | None = None


class SettlementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    party_type: str
    party_id: uuid.UUID
    status: str
    period_start: datetime
    period_end: datetime
    total_paise: int
    currency: str
    report: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class SettlementDetail(SettlementRead):
    ledger_entry_ids: list[uuid.UUID] = Field(default_factory=list)
