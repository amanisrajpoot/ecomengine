"""Tax rule management and GST calculation."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.pricing.schemas import TaxLine
from app.taxation.models import TaxRule
from app.taxation.schemas import (
    TaxCalculateRequest,
    TaxCalculationLine,
    TaxCalculationResult,
    TaxCategory,
    TaxKind,
    TaxRuleCreate,
    TaxRuleUpdate,
)

DEFAULT_RULES: list[dict] = [
    {
        "code": "CGST",
        "category": TaxCategory.GOODS.value,
        "jurisdiction": "IN",
        "rate_bps": 250,
        "inclusive": False,
        "payer": "CUSTOMER",
        "kind": TaxKind.CUSTOMER_TRANSACTION.value,
    },
    {
        "code": "SGST",
        "category": TaxCategory.GOODS.value,
        "jurisdiction": "IN",
        "rate_bps": 250,
        "inclusive": False,
        "payer": "CUSTOMER",
        "kind": TaxKind.CUSTOMER_TRANSACTION.value,
    },
    {
        "code": "CGST",
        "category": TaxCategory.DELIVERY.value,
        "jurisdiction": "IN",
        "rate_bps": 250,
        "inclusive": False,
        "payer": "CUSTOMER",
        "kind": TaxKind.CUSTOMER_TRANSACTION.value,
    },
    {
        "code": "SGST",
        "category": TaxCategory.DELIVERY.value,
        "jurisdiction": "IN",
        "rate_bps": 250,
        "inclusive": False,
        "payer": "CUSTOMER",
        "kind": TaxKind.CUSTOMER_TRANSACTION.value,
    },
]


async def ensure_default_tax_rules(db: AsyncSession) -> None:
    existing = await db.scalar(select(TaxRule.id).limit(1))
    if existing:
        return
    now = datetime.now(timezone.utc)
    for rule in DEFAULT_RULES:
        db.add(
            TaxRule(
                tenant_id=None,
                effective_from=now,
                **rule,
            )
        )
    await db.commit()


async def create_tax_rule(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID | None,
    payload: TaxRuleCreate,
) -> TaxRule:
    now = datetime.now(timezone.utc)
    rule = TaxRule(
        tenant_id=tenant_id,
        code=payload.code.value,
        category=payload.category.value,
        jurisdiction=payload.jurisdiction,
        rate_bps=payload.rate_bps,
        inclusive=payload.inclusive,
        payer=payload.payer.value,
        kind=payload.kind.value,
        effective_from=payload.effective_from or now,
        effective_to=payload.effective_to,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


async def list_tax_rules(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID | None,
    category: str | None = None,
) -> list[TaxRule]:
    now = datetime.now(timezone.utc)
    stmt = select(TaxRule).where(
        or_(TaxRule.tenant_id == tenant_id, TaxRule.tenant_id.is_(None)),
        TaxRule.effective_from <= now,
        or_(TaxRule.effective_to.is_(None), TaxRule.effective_to > now),
    )
    if category:
        stmt = stmt.where(TaxRule.category == category)
    stmt = stmt.order_by(TaxRule.category.asc(), TaxRule.code.asc())
    return list(await db.scalars(stmt))


async def get_tax_rule(
    db: AsyncSession, *, tenant_id: uuid.UUID | None, rule_id: uuid.UUID
) -> TaxRule:
    rule = await db.scalar(
        select(TaxRule).where(
            TaxRule.id == rule_id,
            or_(TaxRule.tenant_id == tenant_id, TaxRule.tenant_id.is_(None)),
        )
    )
    if not rule:
        raise AppError("TAX_RULE_NOT_FOUND", "Tax rule not found", status_code=404)
    return rule


async def update_tax_rule(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID | None,
    rule_id: uuid.UUID,
    payload: TaxRuleUpdate,
) -> TaxRule:
    rule = await get_tax_rule(db, tenant_id=tenant_id, rule_id=rule_id)
    if rule.tenant_id is not None and rule.tenant_id != tenant_id:
        raise AppError("FORBIDDEN", "Cannot update platform default rule", status_code=403)
    data = payload.model_dump(exclude_unset=True, mode="json")
    for key, value in data.items():
        setattr(rule, key, value)
    await db.commit()
    await db.refresh(rule)
    return rule


def _tax_amount_exclusive(taxable_paise: int, rate_bps: int) -> int:
    return (taxable_paise * rate_bps) // 10000


def _tax_amount_inclusive(amount_paise: int, rate_bps: int) -> int:
    if rate_bps <= 0:
        return 0
    return (amount_paise * rate_bps) // (10000 + rate_bps)


async def _active_rules(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    kind: str,
    jurisdiction: str,
) -> list[TaxRule]:
    await ensure_default_tax_rules(db)
    now = datetime.now(timezone.utc)
    rules = list(
        await db.scalars(
            select(TaxRule).where(
                or_(TaxRule.tenant_id == tenant_id, TaxRule.tenant_id.is_(None)),
                TaxRule.kind == kind,
                TaxRule.effective_from <= now,
                or_(TaxRule.effective_to.is_(None), TaxRule.effective_to > now),
                or_(
                    TaxRule.jurisdiction == jurisdiction,
                    TaxRule.jurisdiction == "IN",
                    TaxRule.jurisdiction == "ALL",
                ),
            )
        )
    )
    tenant_rules = [r for r in rules if r.tenant_id == tenant_id]
    platform_rules = [r for r in rules if r.tenant_id is None]
    merged: dict[tuple[str, str, str], TaxRule] = {}
    for rule in platform_rules:
        merged[(rule.category, rule.code, rule.jurisdiction)] = rule
    for rule in tenant_rules:
        merged[(rule.category, rule.code, rule.jurisdiction)] = rule
    return list(merged.values())


async def calculate_tax(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    payload: TaxCalculateRequest,
) -> TaxCalculationResult:
    rules = await _active_rules(
        db,
        tenant_id=tenant_id,
        kind=payload.kind.value,
        jurisdiction=payload.jurisdiction,
    )
    category_amounts = {
        TaxCategory.GOODS.value: payload.goods_taxable_paise,
        TaxCategory.DELIVERY.value: payload.delivery_taxable_paise,
        TaxCategory.PLATFORM_FEE.value: payload.platform_fee_paise,
    }
    lines: list[TaxCalculationLine] = []
    total_tax = 0

    for rule in rules:
        taxable = category_amounts.get(rule.category, 0)
        if taxable <= 0:
            continue
        if rule.inclusive:
            amount = _tax_amount_inclusive(taxable, rule.rate_bps)
        else:
            amount = _tax_amount_exclusive(taxable, rule.rate_bps)
        if amount <= 0:
            continue
        lines.append(
            TaxCalculationLine(
                code=rule.code,
                kind=rule.kind,
                category=rule.category,
                rate_bps=rule.rate_bps,
                taxable_paise=taxable,
                amount_paise=amount,
                payer=rule.payer,
            )
        )
        total_tax += amount

    return TaxCalculationResult(tax_paise=total_tax, lines=lines)


async def calculate_checkout_tax(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    goods_taxable_paise: int,
    delivery_taxable_paise: int,
    platform_fee_paise: int = 0,
    jurisdiction: str = "IN",
) -> tuple[int, list[TaxLine]]:
    result = await calculate_tax(
        db,
        tenant_id=tenant_id,
        payload=TaxCalculateRequest(
            goods_taxable_paise=goods_taxable_paise,
            delivery_taxable_paise=delivery_taxable_paise,
            platform_fee_paise=platform_fee_paise,
            jurisdiction=jurisdiction,
        ),
    )
    tax_lines = [
        TaxLine(code=line.code, rate_bps=line.rate_bps, amount_paise=line.amount_paise)
        for line in result.lines
    ]
    return result.tax_paise, tax_lines
