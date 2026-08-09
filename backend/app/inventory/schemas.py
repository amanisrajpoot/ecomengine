"""Inventory API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, computed_field


class StockReason(StrEnum):
    RECEIVE = "RECEIVE"
    ADJUSTMENT = "ADJUSTMENT"
    RESERVE = "RESERVE"
    RELEASE = "RELEASE"
    CONSUME = "CONSUME"


class InventoryItemUpsert(BaseModel):
    location_id: uuid.UUID
    variant_id: uuid.UUID
    low_stock_threshold: int | None = Field(default=None, ge=0)


class InventoryAdjust(BaseModel):
    """Receive or adjust on_hand via a stock movement (never mutates without movement)."""

    delta_on_hand: int
    reason: StockReason = StockReason.ADJUSTMENT
    note: str | None = None
    reference_type: str | None = None
    reference_id: uuid.UUID | None = None


class InventoryReserve(BaseModel):
    quantity: int = Field(gt=0)
    reference_type: str | None = "cart"
    reference_id: uuid.UUID | None = None
    note: str | None = None


class InventoryRelease(BaseModel):
    quantity: int = Field(gt=0)
    reference_type: str | None = None
    reference_id: uuid.UUID | None = None
    note: str | None = None


class InventoryConsume(BaseModel):
    """Convert reserved stock into a sale (on_hand and reserved both decrease)."""

    quantity: int = Field(gt=0)
    reference_type: str | None = "order"
    reference_id: uuid.UUID | None = None
    note: str | None = None


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

    @computed_field  # type: ignore[prop-decorator]
    @property
    def available(self) -> int:
        return self.on_hand - self.reserved

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_low_stock(self) -> bool:
        if self.low_stock_threshold is None:
            return False
        return self.available <= self.low_stock_threshold

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_out_of_stock(self) -> bool:
        return self.available <= 0


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
    created_at: datetime
    created_by: uuid.UUID | None
    note: str | None
