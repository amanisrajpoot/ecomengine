"""Tax engine schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class TaxLine(BaseModel):
    code: str
    kind: str = "CUSTOMER_TRANSACTION"
    category: str = "GOODS"
    rate_bps: int
    taxable_paise: int
    amount_paise: int
    payer: str = "CUSTOMER"


class TaxCode(StrEnum):
    CGST = "CGST"
    SGST = "SGST"
    IGST = "IGST"
    CESS = "CESS"


class TaxCategory(StrEnum):
    GOODS = "GOODS"
    SERVICE = "SERVICE"
    DELIVERY = "DELIVERY"
    PLATFORM_FEE = "PLATFORM_FEE"
    COMMISSION = "COMMISSION"


class TaxPayer(StrEnum):
    CUSTOMER = "CUSTOMER"
    MERCHANT = "MERCHANT"
    PLATFORM = "PLATFORM"


class TaxKind(StrEnum):
    CUSTOMER_TRANSACTION = "CUSTOMER_TRANSACTION"
    PLATFORM_SERVICE = "PLATFORM_SERVICE"
    SETTLEMENT_DEDUCTION = "SETTLEMENT_DEDUCTION"


class TaxRuleCreate(BaseModel):
    tenant_id: uuid.UUID | None = None
    code: TaxCode
    category: TaxCategory
    jurisdiction: str = "IN-INTRA"
    rate_bps: int = Field(ge=0, le=10000)
    inclusive: bool = False
    payer: TaxPayer = TaxPayer.CUSTOMER
    kind: TaxKind
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    is_active: bool = True


class TaxRuleUpdate(BaseModel):
    rate_bps: int | None = Field(default=None, ge=0, le=10000)
    inclusive: bool | None = None
    payer: TaxPayer | None = None
    jurisdiction: str | None = None
    effective_to: datetime | None = None
    is_active: bool | None = None


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
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TaxCalculationResult(BaseModel):
    tax_paise: int
    lines: list[TaxLine] = Field(default_factory=list)
    kind: str
    category: str
    jurisdiction: str


class TaxCalculateRequest(BaseModel):
    taxable_paise: int = Field(ge=0)
    kind: TaxKind = TaxKind.CUSTOMER_TRANSACTION
    category: TaxCategory = TaxCategory.GOODS
    jurisdiction: str = "IN-INTRA"
    tenant_id: uuid.UUID | None = None
    at: datetime | None = None
