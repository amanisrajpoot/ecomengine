"""Inventory API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, computed_field


class StockReason(StrEnum):
    ADJUSTMENT = "ADJUSTMENT"
    RESERVE = "RESERVE"
    RELEASE = "RELEASE"
    CONSUME = "CONSUME"
    RECEIVE = "RECEIVE"


class InventoryItemCreate(BaseModel):
    variant_id: uuid.UUID
    on_hand: int = Field(ge=0, default=0)
    reserved: int = Field(ge=0, default=0)
    low_stock_threshold: int | None = Field(default=None, ge=0)


class InventoryItemUpdate(BaseModel):
    low_stock_threshold: int | None = Field(default=None, ge=0)


class InventoryItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    business_id: uuid.UUID
    location_id: uuid.UUID
    variant_id: uuid.UUID
    on_hand: int
    reserved: int
    low_stock_threshold: int | None
    updated_at: datetime

    @computed_field
    @property
    def available(self) -> int:
        return self.on_hand - self.reserved


class StockAdjust(BaseModel):
    delta_on_hand: int = 0
    delta_reserved: int = 0
    reason: StockReason = StockReason.ADJUSTMENT
    reference_type: str | None = Field(default=None, max_length=64)
    reference_id: uuid.UUID | None = None


class StockQuantity(BaseModel):
    quantity: int = Field(ge=1)
    reason: StockReason | None = None
    reference_type: str | None = Field(default=None, max_length=64)
    reference_id: uuid.UUID | None = None


class StockMovementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    inventory_item_id: uuid.UUID
    reason: str
    delta_on_hand: int
    delta_reserved: int
    reference_type: str | None
    reference_id: uuid.UUID | None
    created_by: uuid.UUID | None
    created_at: datetime
