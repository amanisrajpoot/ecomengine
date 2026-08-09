"""Tax rule and calculation HTTP routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import AuthContext, require_permission, resolve_tenant_id
from app.taxation import service
from app.taxation.schemas import (
    TaxCalculateRequest,
    TaxCalculationResult,
    TaxRuleCreate,
    TaxRuleRead,
    TaxRuleUpdate,
)

router = APIRouter(prefix="/tax", tags=["tax"])


@router.post("/rules", response_model=TaxRuleRead)
async def create_tax_rule(
    payload: TaxRuleCreate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("tax.manage")),
) -> TaxRuleRead:
    _ = ctx
    rule = await service.create_tax_rule(db, payload)
    return TaxRuleRead.model_validate(rule)


@router.get("/rules", response_model=list[TaxRuleRead])
async def list_tax_rules(
    kind: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("tax.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[TaxRuleRead]:
    _ = ctx
    rows = await service.list_tax_rules(db, tenant_id=tenant_id, kind=kind)
    return [TaxRuleRead.model_validate(r) for r in rows]


@router.patch("/rules/{rule_id}", response_model=TaxRuleRead)
async def update_tax_rule(
    rule_id: uuid.UUID,
    payload: TaxRuleUpdate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("tax.manage")),
) -> TaxRuleRead:
    _ = ctx
    rule = await service.update_tax_rule(db, rule_id, payload)
    return TaxRuleRead.model_validate(rule)


@router.post("/calculate", response_model=TaxCalculationResult)
async def calculate_tax(
    payload: TaxCalculateRequest,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("tax.calculate")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> TaxCalculationResult:
    _ = ctx
    request = payload.model_copy(
        update={"tenant_id": payload.tenant_id or tenant_id}
    )
    return await service.calculate(db, request)


@router.post("/seed-defaults", response_model=list[TaxRuleRead])
async def seed_defaults(
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("tax.manage")),
) -> list[TaxRuleRead]:
    _ = ctx
    rows = await service.seed_india_default_rules(db)
    return [TaxRuleRead.model_validate(r) for r in rows]
