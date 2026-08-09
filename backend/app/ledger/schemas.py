"""Ledger API and posting schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LedgerLineDraft(BaseModel):
    account: str = Field(min_length=2, max_length=64)
    direction: str = Field(pattern=r"^(DEBIT|CREDIT)$")
    amount_paise: int = Field(gt=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class LedgerPostingRequest(BaseModel):
    """Balanced multi-line posting for one financial event."""

    event_type: str = Field(min_length=2, max_length=64)
    reference_key: str = Field(min_length=1, max_length=128)
    order_id: uuid.UUID | None = None
    currency: str = "INR"
    lines: list[LedgerLineDraft] = Field(min_length=2)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def assert_balanced(self) -> LedgerPostingRequest:
        debits = sum(l.amount_paise for l in self.lines if l.direction == "DEBIT")
        credits = sum(l.amount_paise for l in self.lines if l.direction == "CREDIT")
        if debits != credits:
            raise ValueError(f"Unbalanced ledger posting: debits={debits} credits={credits}")
        if debits <= 0:
            raise ValueError("Ledger posting must move a positive amount")
        return self


class ManualAdjustmentBody(BaseModel):
    order_id: uuid.UUID | None = None
    reference_key: str = Field(min_length=1, max_length=128)
    currency: str = "INR"
    lines: list[LedgerLineDraft] = Field(min_length=2)
    reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def assert_balanced(self) -> ManualAdjustmentBody:
        debits = sum(l.amount_paise for l in self.lines if l.direction == "DEBIT")
        credits = sum(l.amount_paise for l in self.lines if l.direction == "CREDIT")
        if debits != credits:
            raise ValueError(f"Unbalanced adjustment: debits={debits} credits={credits}")
        return self


class LedgerEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    order_id: uuid.UUID | None
    event_group_id: uuid.UUID
    event_type: str
    account: str
    direction: str
    amount_paise: int
    currency: str
    reference_key: str
    metadata: dict[str, Any] = Field(validation_alias="metadata_json")
    created_at: datetime
    updated_at: datetime


class LedgerEventRead(BaseModel):
    event_group_id: uuid.UUID
    event_type: str
    reference_key: str
    order_id: uuid.UUID | None
    currency: str
    debit_total_paise: int
    credit_total_paise: int
    entries: list[LedgerEntryRead]


class AccountBalanceRead(BaseModel):
    account: str
    debit_paise: int
    credit_paise: int
    net_paise: int  # credit - debit for liability/revenue; informative only
