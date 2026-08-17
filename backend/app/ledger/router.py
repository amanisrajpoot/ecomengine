"""Ledger HTTP routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import AuthContext, require_permission, resolve_tenant_id
from app.core.errors import AppError
from app.ledger import service
from app.ledger.schemas import LedgerEntryRead, LedgerPostingGroup

router = APIRouter(tags=["ledger"])


def _require_tenant(tenant_id: uuid.UUID | None) -> uuid.UUID:
    if tenant_id is None:
        raise AppError("TENANT_REQUIRED", "X-Tenant-ID header is required", 400)
    return tenant_id


def _group_entries(rows: list) -> list[LedgerPostingGroup]:
    groups: dict[uuid.UUID, LedgerPostingGroup] = {}
    for row in rows:
        entry = LedgerEntryRead.model_validate(row)
        if entry.event_group_id not in groups:
            groups[entry.event_group_id] = LedgerPostingGroup(
                event_group_id=entry.event_group_id,
                event_type=entry.event_type,
                order_id=entry.order_id,
                entries=[],
            )
        groups[entry.event_group_id].entries.append(entry)
    return list(groups.values())


@router.get("/orders/{order_id}/ledger-entries", response_model=list[LedgerPostingGroup])
async def list_order_ledger_entries(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("ledger.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[LedgerPostingGroup]:
    _ = ctx
    tid = _require_tenant(tenant_id)
    rows = await service.list_entries_for_order(db, tenant_id=tid, order_id=order_id)
    return _group_entries(rows)


@router.get("/ledger/event-groups/{event_group_id}", response_model=LedgerPostingGroup)
async def get_ledger_event_group(
    event_group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("ledger.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> LedgerPostingGroup:
    _ = ctx
    tid = _require_tenant(tenant_id)
    rows = await service.list_entries_for_event_group(
        db, tenant_id=tid, event_group_id=event_group_id
    )
    if not rows:
        raise AppError("LEDGER_GROUP_NOT_FOUND", "Ledger event group not found", 404)
    groups = _group_entries(rows)
    return groups[0]
