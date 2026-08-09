"""Tax rule persistence and calculation services."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.taxation.engine import (
    calculate_customer_transaction_tax,
    calculate_tax_from_rules,
    utcnow,
)
from app.taxation.models import TaxRule
from app.taxation.schemas import (
    TaxCalculateRequest,
    TaxCalculationResult,
    TaxCategory,
    TaxCode,
    TaxKind,
    TaxPayer,
    TaxRuleCreate,
    TaxRuleUpdate,
)


async def create_tax_rule(db: AsyncSession, payload: TaxRuleCreate) -> TaxRule:
    rule = TaxRule(
        tenant_id=payload.tenant_id,
        code=payload.code.value,
        category=payload.category.value,
        jurisdiction=payload.jurisdiction,
        rate_bps=payload.rate_bps,
        inclusive=payload.inclusive,
        payer=payload.payer.value,
        kind=payload.kind.value,
        effective_from=payload.effective_from or utcnow(),
        effective_to=payload.effective_to,
        is_active=payload.is_active,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


async def list_tax_rules(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID | None = None,
    kind: str | None = None,
    include_platform_defaults: bool = True,
) -> list[TaxRule]:
    now = utcnow()
    stmt = select(TaxRule).where(TaxRule.is_active.is_(True))
    if include_platform_defaults and tenant_id is not None:
        stmt = stmt.where(or_(TaxRule.tenant_id == tenant_id, TaxRule.tenant_id.is_(None)))
    elif tenant_id is not None:
        stmt = stmt.where(TaxRule.tenant_id == tenant_id)
    elif not include_platform_defaults:
        stmt = stmt.where(TaxRule.tenant_id.is_(None))
    if kind:
        stmt = stmt.where(TaxRule.kind == kind)
    stmt = stmt.where(
        TaxRule.effective_from <= now,
        or_(TaxRule.effective_to.is_(None), TaxRule.effective_to > now),
    )
    stmt = stmt.order_by(TaxRule.kind.asc(), TaxRule.category.asc(), TaxRule.code.asc())
    return list(await db.scalars(stmt))


async def get_tax_rule(db: AsyncSession, rule_id: uuid.UUID) -> TaxRule:
    rule = await db.get(TaxRule, rule_id)
    if not rule:
        raise AppError("TAX_RULE_NOT_FOUND", "Tax rule not found", 404)
    return rule


async def update_tax_rule(
    db: AsyncSession, rule_id: uuid.UUID, payload: TaxRuleUpdate
) -> TaxRule:
    rule = await get_tax_rule(db, rule_id)
    data = payload.model_dump(exclude_unset=True, mode="json")
    for key, value in data.items():
        setattr(rule, key, value)
    await db.commit()
    await db.refresh(rule)
    return rule


async def load_rules_for_calculation(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID | None,
    kind: str,
    at: datetime | None = None,
) -> list[TaxRule]:
    moment = at or utcnow()
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    stmt = select(TaxRule).where(
        TaxRule.is_active.is_(True),
        TaxRule.kind == kind,
        TaxRule.effective_from <= moment,
        or_(TaxRule.effective_to.is_(None), TaxRule.effective_to > moment),
    )
    if tenant_id is not None:
        stmt = stmt.where(or_(TaxRule.tenant_id == tenant_id, TaxRule.tenant_id.is_(None)))
    else:
        stmt = stmt.where(TaxRule.tenant_id.is_(None))
    return list(await db.scalars(stmt))


async def calculate(
    db: AsyncSession, payload: TaxCalculateRequest
) -> TaxCalculationResult:
    rules = await load_rules_for_calculation(
        db,
        tenant_id=payload.tenant_id,
        kind=payload.kind.value,
        at=payload.at,
    )
    if payload.kind == TaxKind.CUSTOMER_TRANSACTION and payload.category == TaxCategory.GOODS:
        return calculate_customer_transaction_tax(
            taxable_paise=payload.taxable_paise,
            jurisdiction=payload.jurisdiction,
            rules=rules,
        )
    result = calculate_tax_from_rules(
        taxable_paise=payload.taxable_paise,
        kind=payload.kind.value,
        category=payload.category.value,
        jurisdiction=payload.jurisdiction,
        rules=rules,
    )
    if not result.lines and payload.kind != TaxKind.CUSTOMER_TRANSACTION:
        # No silent GST blob — empty result means no configured rules.
        return result
    if not result.lines and payload.kind == TaxKind.CUSTOMER_TRANSACTION:
        return calculate_customer_transaction_tax(
            taxable_paise=payload.taxable_paise,
            jurisdiction=payload.jurisdiction,
            rules=None,
        )
    return result


async def seed_india_default_rules(db: AsyncSession) -> list[TaxRule]:
    """Platform-default India GST rules (tenant_id NULL). Idempotent by code/kind/category/jurisdiction."""
    defaults = [
        TaxRuleCreate(
            code=TaxCode.CGST,
            category=TaxCategory.GOODS,
            jurisdiction="IN-INTRA",
            rate_bps=250,
            payer=TaxPayer.CUSTOMER,
            kind=TaxKind.CUSTOMER_TRANSACTION,
        ),
        TaxRuleCreate(
            code=TaxCode.SGST,
            category=TaxCategory.GOODS,
            jurisdiction="IN-INTRA",
            rate_bps=250,
            payer=TaxPayer.CUSTOMER,
            kind=TaxKind.CUSTOMER_TRANSACTION,
        ),
        TaxRuleCreate(
            code=TaxCode.IGST,
            category=TaxCategory.GOODS,
            jurisdiction="IN-INTER",
            rate_bps=500,
            payer=TaxPayer.CUSTOMER,
            kind=TaxKind.CUSTOMER_TRANSACTION,
        ),
        TaxRuleCreate(
            code=TaxCode.CGST,
            category=TaxCategory.COMMISSION,
            jurisdiction="IN-INTRA",
            rate_bps=900,
            payer=TaxPayer.MERCHANT,
            kind=TaxKind.PLATFORM_SERVICE,
        ),
        TaxRuleCreate(
            code=TaxCode.SGST,
            category=TaxCategory.COMMISSION,
            jurisdiction="IN-INTRA",
            rate_bps=900,
            payer=TaxPayer.MERCHANT,
            kind=TaxKind.PLATFORM_SERVICE,
        ),
        TaxRuleCreate(
            code=TaxCode.CGST,
            category=TaxCategory.COMMISSION,
            jurisdiction="IN-INTRA",
            rate_bps=900,
            payer=TaxPayer.MERCHANT,
            kind=TaxKind.SETTLEMENT_DEDUCTION,
        ),
        TaxRuleCreate(
            code=TaxCode.SGST,
            category=TaxCategory.COMMISSION,
            jurisdiction="IN-INTRA",
            rate_bps=900,
            payer=TaxPayer.MERCHANT,
            kind=TaxKind.SETTLEMENT_DEDUCTION,
        ),
    ]
    created: list[TaxRule] = []
    for spec in defaults:
        existing = await db.scalar(
            select(TaxRule).where(
                TaxRule.tenant_id.is_(None),
                TaxRule.code == spec.code.value,
                TaxRule.category == spec.category.value,
                TaxRule.jurisdiction == spec.jurisdiction,
                TaxRule.kind == spec.kind.value,
                TaxRule.is_active.is_(True),
            )
        )
        if existing:
            created.append(existing)
            continue
        created.append(await create_tax_rule(db, spec))
    return created
