"""Pricing breakdown schemas."""

from __future__ import annotations

from typing import Any

import uuid

from pydantic import BaseModel, Field, model_validator


class TaxLine(BaseModel):
    code: str
    rate_bps: int = Field(ge=0)
    amount_paise: int = Field(ge=0)


class PriceLine(BaseModel):
    cart_item_id: str | None = None
    variant_id: str | None = None
    bundle_id: str | None = None
    name: str
    quantity: int = Field(ge=1)
    unit_price_paise: int = Field(ge=0)
    line_total_paise: int = Field(ge=0)
    addons: list[dict[str, Any]] = Field(default_factory=list)


class PriceBreakdown(BaseModel):
    currency: str = "INR"
    subtotal_paise: int = Field(ge=0)
    discount_paise: int = Field(ge=0, default=0)
    delivery_fee_paise: int = Field(ge=0, default=0)
    platform_fee_paise: int = Field(ge=0, default=0)
    other_fees_paise: int = Field(ge=0, default=0)
    tax_paise: int = Field(ge=0, default=0)
    tax_lines: list[TaxLine] = Field(default_factory=list)
    total_paise: int = Field(ge=0)
    lines: list[PriceLine] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_total(self) -> PriceBreakdown:
        expected = (
            self.subtotal_paise
            - self.discount_paise
            + self.delivery_fee_paise
            + self.platform_fee_paise
            + self.other_fees_paise
            + self.tax_paise
        )
        if self.total_paise != expected:
            raise ValueError(f"total_paise {self.total_paise} != expected {expected}")
        return self


class CourierAddress(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    address: dict[str, Any] = Field(default_factory=dict)


class CourierQuoteRequest(BaseModel):
    business_id: uuid.UUID
    pickup: CourierAddress
    drop: CourierAddress
    weight_kg: float = Field(gt=0, le=500)
    vehicle_type: str = Field(default="BIKE", min_length=1, max_length=16)
    express: bool = False


class CourierQuoteResponse(BaseModel):
    breakdown: PriceBreakdown
    quote: dict[str, Any]
