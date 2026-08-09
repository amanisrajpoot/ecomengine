"""Ledger HTTP routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import AuthContext, require_permission, resolve_tenant_id
from app.core.errors import AppError
from app.ledger import service
from app.ledger.schemas import (
    AccountBalanceRead,
    LedgerEntryRead,
    LedgerEventRead,
    ManualAdjustmentBody,
)

router = APIRouter(tags=["ledger"])


def _require_tenant(tenant_id: uuid.UUID | None) -> uuid.UUID:
    if tenant_id is None:
        raise AppError("TENANT_REQUIRED", "X-Tenant-ID header is required", 400)
    return tenant_id


@router.get("/ledger/entries", response_model=list[LedgerEntryRead])
async def list_ledger_entries(
    order_id: uuid.UUID | None = None,
    account: str | None = None,
    event_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("ledger.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[LedgerEntryRead]:
    _ = ctx
    tid = _require_tenant(tenant_id)
    rows = await service.list_entries(
        db,
        tenant_id=tid,
        order_id=order_id,
        account=account,
        event_type=event_type,
    )
    return [LedgerEntryRead.model_validate(r) for r in rows]


@router.get("/orders/{order_id}/ledger", response_model=list[LedgerEntryRead])
async def list_order_ledger(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("ledger.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[LedgerEntryRead]:
    _ = ctx
    tid = _require_tenant(tenant_id)
    rows = await service.list_entries(db, tenant_id=tid, order_id=order_id)
    return [LedgerEntryRead.model_validate(r) for r in rows]


@router.get("/ledger/events/{event_group_id}", response_model=LedgerEventRead)
async def get_ledger_event(
    event_group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("ledger.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> LedgerEventRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    return await service.get_event_group(db, tenant_id=tid, event_group_id=event_group_id)


@router.get("/ledger/balances", response_model=list[AccountBalanceRead])
async def list_account_balances(
    order_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("ledger.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[AccountBalanceRead]:
    _ = ctx
    tid = _require_tenant(tenant_id)
    return await service.account_balances(db, tenant_id=tid, order_id=order_id)


@router.post("/ledger/adjustments", response_model=LedgerEventRead)
async def create_manual_adjustment(
    payload: ManualAdjustmentBody,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("ledger.adjust")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> LedgerEventRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    entries = await service.post_manual_adjustment(db, tenant_id=tid, payload=payload)
    return await service.get_event_group(
        db, tenant_id=tid, event_group_id=entries[0].event_group_id
    )
