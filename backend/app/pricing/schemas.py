"""Pricing breakdown contracts (integer paise)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TaxLine(BaseModel):
    code: str
    kind: str = "CUSTOMER_TRANSACTION"
    category: str = "GOODS"
    rate_bps: int
    taxable_paise: int
    amount_paise: int
    payer: str = "CUSTOMER"


class PriceLine(BaseModel):
    variant_id: str | None = None
    bundle_id: str | None = None
    name: str
    quantity: int
    unit_price_paise: int
    modifiers_paise: int = 0
    line_subtotal_paise: int
    addons: list[dict[str, Any]] = Field(default_factory=list)


class PriceBreakdown(BaseModel):
    currency: str = "INR"
    subtotal_paise: int
    discount_paise: int = 0
    delivery_fee_paise: int = 0
    platform_fee_paise: int = 0
    other_fees_paise: int = 0
    tax_paise: int = 0
    tax_lines: list[TaxLine] = Field(default_factory=list)
    total_paise: int
    lines: list[PriceLine] = Field(default_factory=list)

    def assert_invariant(self) -> None:
        expected = (
            self.subtotal_paise
            - self.discount_paise
            + self.delivery_fee_paise
            + self.platform_fee_paise
            + self.other_fees_paise
            + self.tax_paise
        )
        if expected != self.total_paise:
            raise ValueError(
                f"Price breakdown invariant failed: expected {expected}, got {self.total_paise}"
            )


class PricingInputItem(BaseModel):
    name: str
    quantity: int = Field(ge=1)
    unit_price_paise: int = Field(ge=0)
    modifiers_paise: int = Field(ge=0, default=0)
    variant_id: str | None = None
    bundle_id: str | None = None
    addons: list[dict[str, Any]] = Field(default_factory=list)


class PricingContext(BaseModel):
    currency: str = "INR"
    discount_paise: int = Field(ge=0, default=0)
    delivery_fee_paise: int = Field(ge=0, default=0)
    platform_fee_paise: int = Field(ge=0, default=0)
    other_fees_paise: int = Field(ge=0, default=0)
    # Used by Phase 5 tax stub; Phase 6 TaxRule engine will supersede.
    tax_rate_bps: int = Field(ge=0, default=500)
    tax_jurisdiction: str = "IN-INTRA"
