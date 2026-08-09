"""Inventory HTTP routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import AuthContext, require_permission, resolve_tenant_id
from app.core.errors import AppError
from app.inventory import service
from app.inventory.schemas import (
    InventoryAdjust,
    InventoryConsume,
    InventoryItemRead,
    InventoryItemUpsert,
    InventoryRelease,
    InventoryReserve,
    StockMovementRead,
)

router = APIRouter(tags=["inventory"])


def _require_tenant(tenant_id: uuid.UUID | None) -> uuid.UUID:
    if tenant_id is None:
        raise AppError("TENANT_REQUIRED", "X-Tenant-ID header is required", 400)
    return tenant_id


@router.post(
    "/businesses/{business_id}/inventory",
    response_model=InventoryItemRead,
)
async def upsert_inventory_item(
    business_id: uuid.UUID,
    payload: InventoryItemUpsert,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("inventory.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> InventoryItemRead:
    tid = _require_tenant(tenant_id)
    item = await service.upsert_inventory_item(
        db, tenant_id=tid, business_id=business_id, payload=payload
    )
    _ = ctx
    return InventoryItemRead.model_validate(item)


@router.get(
    "/businesses/{business_id}/inventory",
    response_model=list[InventoryItemRead],
)
async def list_inventory(
    business_id: uuid.UUID,
    location_id: uuid.UUID | None = Query(default=None),
    low_stock_only: bool = Query(default=False),
    out_of_stock_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("inventory.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[InventoryItemRead]:
    _ = ctx
    tid = _require_tenant(tenant_id)
    items = await service.list_inventory(
        db,
        tenant_id=tid,
        business_id=business_id,
        location_id=location_id,
        low_stock_only=low_stock_only,
        out_of_stock_only=out_of_stock_only,
    )
    return [InventoryItemRead.model_validate(i) for i in items]


@router.get(
    "/businesses/{business_id}/inventory/{item_id}",
    response_model=InventoryItemRead,
)
async def get_inventory_item(
    business_id: uuid.UUID,
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("inventory.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> InventoryItemRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    item = await service.get_inventory_item(
        db, tenant_id=tid, business_id=business_id, item_id=item_id
    )
    return InventoryItemRead.model_validate(item)


@router.post(
    "/businesses/{business_id}/inventory/{item_id}/adjust",
    response_model=InventoryItemRead,
)
async def adjust_stock(
    business_id: uuid.UUID,
    item_id: uuid.UUID,
    payload: InventoryAdjust,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("inventory.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> InventoryItemRead:
    tid = _require_tenant(tenant_id)
    item, _movement = await service.adjust_stock(
        db,
        tenant_id=tid,
        business_id=business_id,
        item_id=item_id,
        payload=payload,
        actor_user_id=ctx.user.id,
    )
    return InventoryItemRead.model_validate(item)


@router.post(
    "/businesses/{business_id}/inventory/{item_id}/reserve",
    response_model=InventoryItemRead,
)
async def reserve_stock(
    business_id: uuid.UUID,
    item_id: uuid.UUID,
    payload: InventoryReserve,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("inventory.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> InventoryItemRead:
    tid = _require_tenant(tenant_id)
    item, _movement = await service.reserve_stock(
        db,
        tenant_id=tid,
        business_id=business_id,
        item_id=item_id,
        payload=payload,
        actor_user_id=ctx.user.id,
    )
    return InventoryItemRead.model_validate(item)


@router.post(
    "/businesses/{business_id}/inventory/{item_id}/release",
    response_model=InventoryItemRead,
)
async def release_stock(
    business_id: uuid.UUID,
    item_id: uuid.UUID,
    payload: InventoryRelease,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("inventory.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> InventoryItemRead:
    tid = _require_tenant(tenant_id)
    item, _movement = await service.release_stock(
        db,
        tenant_id=tid,
        business_id=business_id,
        item_id=item_id,
        payload=payload,
        actor_user_id=ctx.user.id,
    )
    return InventoryItemRead.model_validate(item)


@router.post(
    "/businesses/{business_id}/inventory/{item_id}/consume",
    response_model=InventoryItemRead,
)
async def consume_stock(
    business_id: uuid.UUID,
    item_id: uuid.UUID,
    payload: InventoryConsume,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("inventory.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> InventoryItemRead:
    tid = _require_tenant(tenant_id)
    item, _movement = await service.consume_stock(
        db,
        tenant_id=tid,
        business_id=business_id,
        item_id=item_id,
        payload=payload,
        actor_user_id=ctx.user.id,
    )
    return InventoryItemRead.model_validate(item)


@router.get(
    "/businesses/{business_id}/inventory/{item_id}/movements",
    response_model=list[StockMovementRead],
)
async def list_movements(
    business_id: uuid.UUID,
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("inventory.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[StockMovementRead]:
    _ = ctx
    tid = _require_tenant(tenant_id)
    rows = await service.list_movements(
        db, tenant_id=tid, business_id=business_id, item_id=item_id
    )
    return [StockMovementRead.model_validate(r) for r in rows]
