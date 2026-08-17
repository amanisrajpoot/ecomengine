"""Taxation HTTP routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import AuthContext, require_permission, resolve_tenant_id
from app.core.errors import AppError
from app.taxation import service
from app.taxation.schemas import (
    TaxCalculateRequest,
    TaxCalculationResult,
    TaxRuleCreate,
    TaxRuleRead,
    TaxRuleUpdate,
)

router = APIRouter(tags=["taxation"])


def _require_tenant(tenant_id: uuid.UUID | None) -> uuid.UUID:
    if tenant_id is None:
        raise AppError("TENANT_REQUIRED", "X-Tenant-ID header is required", 400)
    return tenant_id


@router.post("/tax-rules", response_model=TaxRuleRead)
async def create_tax_rule(
    payload: TaxRuleCreate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("taxes.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> TaxRuleRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    rule = await service.create_tax_rule(db, tenant_id=tid, payload=payload)
    return TaxRuleRead.model_validate(rule)


@router.get("/tax-rules", response_model=list[TaxRuleRead])
async def list_tax_rules(
    category: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("taxes.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[TaxRuleRead]:
    _ = ctx
    tid = _require_tenant(tenant_id)
    rows = await service.list_tax_rules(db, tenant_id=tid, category=category)
    return [TaxRuleRead.model_validate(r) for r in rows]


@router.patch("/tax-rules/{rule_id}", response_model=TaxRuleRead)
async def update_tax_rule(
    rule_id: uuid.UUID,
    payload: TaxRuleUpdate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("taxes.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> TaxRuleRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    rule = await service.update_tax_rule(
        db, tenant_id=tid, rule_id=rule_id, payload=payload
    )
    return TaxRuleRead.model_validate(rule)


@router.post("/tax/calculate", response_model=TaxCalculationResult)
async def calculate_tax(
    payload: TaxCalculateRequest,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("taxes.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> TaxCalculationResult:
    _ = ctx
    tid = _require_tenant(tenant_id)
    return await service.calculate_tax(db, tenant_id=tid, payload=payload)
