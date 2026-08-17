"""Settlement HTTP routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import AuthContext, require_permission, resolve_tenant_id
from app.core.errors import AppError
from app.settlements import service
from app.settlements.schemas import (
    SettlementCalculate,
    SettlementDetail,
    SettlementRead,
    SettlementTransition,
)

router = APIRouter(tags=["settlements"])


def _require_tenant(tenant_id: uuid.UUID | None) -> uuid.UUID:
    if tenant_id is None:
        raise AppError("TENANT_REQUIRED", "X-Tenant-ID header is required", 400)
    return tenant_id


@router.post("/settlements/calculate", response_model=SettlementRead)
async def calculate_settlement(
    payload: SettlementCalculate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("settlements.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> SettlementRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    settlement = await service.calculate_settlement(db, tenant_id=tid, payload=payload)
    return SettlementRead.model_validate(settlement)


@router.get("/settlements", response_model=list[SettlementRead])
async def list_settlements(
    party_type: str | None = Query(default=None),
    party_id: uuid.UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("settlements.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[SettlementRead]:
    _ = ctx
    tid = _require_tenant(tenant_id)
    rows = await service.list_settlements(
        db,
        tenant_id=tid,
        party_type=party_type,
        party_id=party_id,
        status=status,
    )
    return [SettlementRead.model_validate(r) for r in rows]


@router.get("/settlements/{settlement_id}", response_model=SettlementDetail)
async def get_settlement(
    settlement_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("settlements.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> SettlementDetail:
    _ = ctx
    tid = _require_tenant(tenant_id)
    settlement, entry_ids = await service.get_settlement(
        db, tenant_id=tid, settlement_id=settlement_id
    )
    return SettlementDetail(
        **SettlementRead.model_validate(settlement).model_dump(),
        ledger_entry_ids=entry_ids,
    )


@router.get("/orders/{order_id}/settlements", response_model=list[SettlementRead])
async def list_order_settlements(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("settlements.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[SettlementRead]:
    _ = ctx
    tid = _require_tenant(tenant_id)
    rows = await service.list_settlements_for_order(db, tenant_id=tid, order_id=order_id)
    return [SettlementRead.model_validate(r) for r in rows]


@router.post("/settlements/{settlement_id}/transition", response_model=SettlementRead)
async def transition_settlement(
    settlement_id: uuid.UUID,
    payload: SettlementTransition,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("settlements.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> SettlementRead:
    tid = _require_tenant(tenant_id)
    settlement = await service.transition_settlement(
        db,
        tenant_id=tid,
        settlement_id=settlement_id,
        payload=payload,
        actor_user_id=ctx.user.id,
    )
    return SettlementRead.model_validate(settlement)
