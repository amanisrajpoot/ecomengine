"""Taxation module — Phase 5 stub; Phase 6 replaces with TaxRule engine."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.pricing.schemas import TaxLine


class TaxCalculationResult(BaseModel):
    tax_paise: int
    lines: list[TaxLine] = Field(default_factory=list)


def calculate_customer_transaction_tax(
    *,
    taxable_paise: int,
    rate_bps: int = 500,
    jurisdiction: str = "IN-INTRA",
) -> TaxCalculationResult:
    """
    India V1 stub:
    - Intra-state: split rate evenly into CGST + SGST
    - Inter-state: single IGST line
    Full TaxRule persistence arrives in Phase 6.
    """
    if taxable_paise <= 0 or rate_bps <= 0:
        return TaxCalculationResult(tax_paise=0, lines=[])

    total_tax = (taxable_paise * rate_bps) // 10_000

    if jurisdiction.upper() in {"IN-INTER", "IGST"}:
        lines = [
            TaxLine(
                code="IGST",
                kind="CUSTOMER_TRANSACTION",
                category="GOODS",
                rate_bps=rate_bps,
                taxable_paise=taxable_paise,
                amount_paise=total_tax,
                payer="CUSTOMER",
            )
        ]
        return TaxCalculationResult(tax_paise=total_tax, lines=lines)

    half_bps = rate_bps // 2
    # Allocate remainder paise to SGST to keep sum exact.
    cgst = (taxable_paise * half_bps) // 10_000
    sgst = total_tax - cgst
    lines = [
        TaxLine(
            code="CGST",
            kind="CUSTOMER_TRANSACTION",
            category="GOODS",
            rate_bps=half_bps,
            taxable_paise=taxable_paise,
            amount_paise=cgst,
            payer="CUSTOMER",
        ),
        TaxLine(
            code="SGST",
            kind="CUSTOMER_TRANSACTION",
            category="GOODS",
            rate_bps=rate_bps - half_bps,
            taxable_paise=taxable_paise,
            amount_paise=sgst,
            payer="CUSTOMER",
        ),
    ]
    return TaxCalculationResult(tax_paise=total_tax, lines=lines)
