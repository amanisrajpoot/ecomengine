"""Taxation API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class TaxCode(StrEnum):
    CGST = "CGST"
    SGST = "SGST"
    IGST = "IGST"


class TaxCategory(StrEnum):
    GOODS = "GOODS"
    SERVICE = "SERVICE"
    DELIVERY = "DELIVERY"
    PLATFORM_FEE = "PLATFORM_FEE"
    COMMISSION = "COMMISSION"


class TaxKind(StrEnum):
    CUSTOMER_TRANSACTION = "CUSTOMER_TRANSACTION"
    PLATFORM_SERVICE = "PLATFORM_SERVICE"
    SETTLEMENT_DEDUCTION = "SETTLEMENT_DEDUCTION"


class TaxPayer(StrEnum):
    CUSTOMER = "CUSTOMER"
    MERCHANT = "MERCHANT"
    PLATFORM = "PLATFORM"


class TaxRuleCreate(BaseModel):
    code: TaxCode
    category: TaxCategory
    jurisdiction: str = "IN"
    rate_bps: int = Field(ge=0, le=10000)
    inclusive: bool = False
    payer: TaxPayer = TaxPayer.CUSTOMER
    kind: TaxKind = TaxKind.CUSTOMER_TRANSACTION
    effective_from: datetime | None = None
    effective_to: datetime | None = None


class TaxRuleUpdate(BaseModel):
    code: TaxCode | None = None
    category: TaxCategory | None = None
    jurisdiction: str | None = None
    rate_bps: int | None = Field(default=None, ge=0, le=10000)
    inclusive: bool | None = None
    payer: TaxPayer | None = None
    kind: TaxKind | None = None
    effective_from: datetime | None = None
    effective_to: datetime | None = None


class TaxRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID | None
    code: str
    category: str
    jurisdiction: str
    rate_bps: int
    inclusive: bool
    payer: str
    kind: str
    effective_from: datetime
    effective_to: datetime | None
    created_at: datetime
    updated_at: datetime


class TaxCalculationLine(BaseModel):
    code: str
    kind: str
    category: str
    rate_bps: int
    taxable_paise: int
    amount_paise: int
    payer: str


class TaxCalculationResult(BaseModel):
    tax_paise: int
    lines: list[TaxCalculationLine]


class TaxCalculateRequest(BaseModel):
    goods_taxable_paise: int = Field(ge=0, default=0)
    delivery_taxable_paise: int = Field(ge=0, default=0)
    platform_fee_paise: int = Field(ge=0, default=0)
    jurisdiction: str = "IN"
    kind: TaxKind = TaxKind.CUSTOMER_TRANSACTION
