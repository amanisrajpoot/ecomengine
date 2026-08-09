"""Settlement HTTP routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import AuthContext, require_permission, resolve_tenant_id
from app.core.errors import AppError
from app.settlements import service
from app.settlements.access import (
    assert_settlement_read_readable,
    is_merchant_settlement_viewer,
    merchant_business_ids,
)
from app.settlements.schemas import SettlementCreate, SettlementRead, SettlementTransitionBody

router = APIRouter(tags=["settlements"])


def _require_tenant(tenant_id: uuid.UUID | None) -> uuid.UUID:
    if tenant_id is None:
        raise AppError("TENANT_REQUIRED", "X-Tenant-ID header is required", 400)
    return tenant_id


@router.post("/settlements", response_model=SettlementRead)
async def create_settlement(
    payload: SettlementCreate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("settlements.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> SettlementRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    settlement = await service.create_settlement(db, tenant_id=tid, payload=payload)
    return await service.to_read(db, settlement)


@router.get("/settlements", response_model=list[SettlementRead])
async def list_settlements(
    party_type: str | None = None,
    party_id: uuid.UUID | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("settlements.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[SettlementRead]:
    tid = _require_tenant(tenant_id)
    scoped_party_type = party_type
    scoped_party_id = party_id
    scoped_party_ids: list[uuid.UUID] | None = None
    if is_merchant_settlement_viewer(ctx):
        scoped_party_type = "MERCHANT"
        scoped_party_ids = merchant_business_ids(ctx)
        if not scoped_party_ids:
            return []
        if party_id and party_id not in scoped_party_ids:
            return []
        if party_id:
            scoped_party_id = party_id
            scoped_party_ids = None
    rows = await service.list_settlements(
        db,
        tenant_id=tid,
        party_type=scoped_party_type,
        party_id=scoped_party_id,
        party_ids=scoped_party_ids,
        status=status,
    )
    return [await service.to_read(db, r) for r in rows]


@router.get("/settlements/{settlement_id}", response_model=SettlementRead)
async def get_settlement(
    settlement_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("settlements.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> SettlementRead:
    tid = _require_tenant(tenant_id)
    read = await service.get_settlement(db, tenant_id=tid, settlement_id=settlement_id)
    assert_settlement_read_readable(ctx, party_type=read.party_type, party_id=read.party_id)
    return read


@router.post("/settlements/{settlement_id}/calculate", response_model=SettlementRead)
async def calculate_settlement(
    settlement_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("settlements.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> SettlementRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    return await service.calculate_settlement(
        db, tenant_id=tid, settlement_id=settlement_id
    )


@router.post("/settlements/{settlement_id}/reconcile", response_model=SettlementRead)
async def reconcile_settlement(
    settlement_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("settlements.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> SettlementRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    return await service.reconcile_settlement(
        db, tenant_id=tid, settlement_id=settlement_id
    )


@router.post("/settlements/{settlement_id}/approve", response_model=SettlementRead)
async def approve_settlement(
    settlement_id: uuid.UUID,
    payload: SettlementTransitionBody | None = None,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("settlements.approve")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> SettlementRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    return await service.approve_settlement(
        db,
        tenant_id=tid,
        settlement_id=settlement_id,
        reason=(payload.reason if payload else None),
    )


@router.post("/settlements/{settlement_id}/mark-paid", response_model=SettlementRead)
async def mark_settlement_paid(
    settlement_id: uuid.UUID,
    payload: SettlementTransitionBody | None = None,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("settlements.approve")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> SettlementRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    return await service.mark_settlement_paid(
        db,
        tenant_id=tid,
        settlement_id=settlement_id,
        reason=(payload.reason if payload else None),
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
    if is_merchant_settlement_viewer(ctx):
        allowed = set(merchant_business_ids(ctx))
        rows = [r for r in rows if r.party_type == "MERCHANT" and r.party_id in allowed]
    return rows
