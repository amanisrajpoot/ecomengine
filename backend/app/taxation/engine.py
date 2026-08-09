"""Tax calculation engine driven by TaxRule rows."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from app.taxation.schemas import TaxCalculationResult, TaxCategory, TaxKind, TaxLine


class TaxRuleLike(Protocol):
    code: str
    category: str
    jurisdiction: str
    rate_bps: int
    inclusive: bool
    payer: str
    kind: str


def _amount_for_rate(taxable_paise: int, rate_bps: int, *, inclusive: bool) -> int:
    if taxable_paise <= 0 or rate_bps <= 0:
        return 0
    if inclusive:
        # Extract tax already embedded in price: tax = price - price/(1+r)
        # amount = taxable * rate / (10000 + rate)
        return (taxable_paise * rate_bps) // (10_000 + rate_bps)
    return (taxable_paise * rate_bps) // 10_000


def filter_applicable_rules(
    rules: list[TaxRuleLike],
    *,
    kind: str,
    category: str,
    jurisdiction: str,
) -> list[TaxRuleLike]:
    jurisdiction_u = jurisdiction.upper()
    matched = [
        r
        for r in rules
        if r.kind == kind
        and r.category == category
        and r.jurisdiction.upper() in {jurisdiction_u, "ALL", "IN"}
    ]
    # Prefer exact jurisdiction over ALL/IN when both exist for same code.
    exact = [r for r in matched if r.jurisdiction.upper() == jurisdiction_u]
    return exact or matched


def calculate_tax_from_rules(
    *,
    taxable_paise: int,
    kind: str,
    category: str,
    jurisdiction: str,
    rules: list[TaxRuleLike],
) -> TaxCalculationResult:
    applicable = filter_applicable_rules(
        rules, kind=kind, category=category, jurisdiction=jurisdiction
    )
    lines: list[TaxLine] = []
    total = 0
    for rule in applicable:
        # Inclusive rules adjust taxable base interpretation per line; V1 applies
        # each exclusive rule on the provided taxable_paise independently.
        amount = _amount_for_rate(taxable_paise, rule.rate_bps, inclusive=rule.inclusive)
        if amount <= 0 and rule.rate_bps <= 0:
            continue
        lines.append(
            TaxLine(
                code=rule.code,
                kind=rule.kind,
                category=rule.category,
                rate_bps=rule.rate_bps,
                taxable_paise=taxable_paise,
                amount_paise=amount,
                payer=rule.payer,
            )
        )
        total += amount

    return TaxCalculationResult(
        tax_paise=total,
        lines=lines,
        kind=kind,
        category=category,
        jurisdiction=jurisdiction,
    )


def fallback_customer_transaction_tax(
    *,
    taxable_paise: int,
    rate_bps: int = 500,
    jurisdiction: str = "IN-INTRA",
) -> TaxCalculationResult:
    """Used only when no TaxRules are configured."""
    if taxable_paise <= 0 or rate_bps <= 0:
        return TaxCalculationResult(
            tax_paise=0,
            lines=[],
            kind=TaxKind.CUSTOMER_TRANSACTION.value,
            category=TaxCategory.GOODS.value,
            jurisdiction=jurisdiction,
        )

    total_tax = (taxable_paise * rate_bps) // 10_000
    if jurisdiction.upper() in {"IN-INTER", "IGST"}:
        return TaxCalculationResult(
            tax_paise=total_tax,
            lines=[
                TaxLine(
                    code="IGST",
                    kind=TaxKind.CUSTOMER_TRANSACTION.value,
                    category=TaxCategory.GOODS.value,
                    rate_bps=rate_bps,
                    taxable_paise=taxable_paise,
                    amount_paise=total_tax,
                    payer="CUSTOMER",
                )
            ],
            kind=TaxKind.CUSTOMER_TRANSACTION.value,
            category=TaxCategory.GOODS.value,
            jurisdiction=jurisdiction,
        )

    half_bps = rate_bps // 2
    cgst = (taxable_paise * half_bps) // 10_000
    sgst = total_tax - cgst
    return TaxCalculationResult(
        tax_paise=total_tax,
        lines=[
            TaxLine(
                code="CGST",
                kind=TaxKind.CUSTOMER_TRANSACTION.value,
                category=TaxCategory.GOODS.value,
                rate_bps=half_bps,
                taxable_paise=taxable_paise,
                amount_paise=cgst,
                payer="CUSTOMER",
            ),
            TaxLine(
                code="SGST",
                kind=TaxKind.CUSTOMER_TRANSACTION.value,
                category=TaxCategory.GOODS.value,
                rate_bps=rate_bps - half_bps,
                taxable_paise=taxable_paise,
                amount_paise=sgst,
                payer="CUSTOMER",
            ),
        ],
        kind=TaxKind.CUSTOMER_TRANSACTION.value,
        category=TaxCategory.GOODS.value,
        jurisdiction=jurisdiction,
    )


def calculate_customer_transaction_tax(
    *,
    taxable_paise: int,
    rate_bps: int = 500,
    jurisdiction: str = "IN-INTRA",
    rules: list[TaxRuleLike] | None = None,
) -> TaxCalculationResult:
    if rules:
        result = calculate_tax_from_rules(
            taxable_paise=taxable_paise,
            kind=TaxKind.CUSTOMER_TRANSACTION.value,
            category=TaxCategory.GOODS.value,
            jurisdiction=jurisdiction,
            rules=rules,
        )
        if result.lines:
            return result
    return fallback_customer_transaction_tax(
        taxable_paise=taxable_paise, rate_bps=rate_bps, jurisdiction=jurisdiction
    )


def utcnow() -> datetime:
    return datetime.now(UTC)
