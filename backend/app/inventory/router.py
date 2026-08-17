"""Inventory HTTP routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import AuthContext, require_permission, resolve_tenant_id
from app.core.errors import AppError
from app.inventory import service
from app.inventory.schemas import (
    InventoryItemCreate,
    InventoryItemRead,
    InventoryItemUpdate,
    StockAdjust,
    StockMovementRead,
    StockQuantity,
)

router = APIRouter(tags=["inventory"])


def _require_tenant(tenant_id: uuid.UUID | None) -> uuid.UUID:
    if tenant_id is None:
        raise AppError("TENANT_REQUIRED", "X-Tenant-ID header is required", 400)
    return tenant_id


@router.post(
    "/businesses/{business_id}/locations/{location_id}/inventory-items",
    response_model=InventoryItemRead,
)
async def create_inventory_item(
    business_id: uuid.UUID,
    location_id: uuid.UUID,
    payload: InventoryItemCreate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("inventory.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> InventoryItemRead:
    tid = _require_tenant(tenant_id)
    item = await service.create_inventory_item(
        db,
        tenant_id=tid,
        business_id=business_id,
        location_id=location_id,
        payload=payload,
        actor_user_id=ctx.user.id,
    )
    return InventoryItemRead.model_validate(item)


@router.get(
    "/businesses/{business_id}/locations/{location_id}/inventory-items",
    response_model=list[InventoryItemRead],
)
async def list_inventory_items(
    business_id: uuid.UUID,
    location_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("inventory.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[InventoryItemRead]:
    _ = ctx
    tid = _require_tenant(tenant_id)
    rows = await service.list_inventory_items(
        db, tenant_id=tid, business_id=business_id, location_id=location_id
    )
    return [InventoryItemRead.model_validate(r) for r in rows]


@router.get(
    "/businesses/{business_id}/locations/{location_id}/inventory-items/{inventory_item_id}",
    response_model=InventoryItemRead,
)
async def get_inventory_item(
    business_id: uuid.UUID,
    location_id: uuid.UUID,
    inventory_item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("inventory.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> InventoryItemRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    item = await service.get_inventory_item(
        db,
        tenant_id=tid,
        business_id=business_id,
        location_id=location_id,
        inventory_item_id=inventory_item_id,
    )
    return InventoryItemRead.model_validate(item)


@router.patch(
    "/businesses/{business_id}/locations/{location_id}/inventory-items/{inventory_item_id}",
    response_model=InventoryItemRead,
)
async def update_inventory_item(
    business_id: uuid.UUID,
    location_id: uuid.UUID,
    inventory_item_id: uuid.UUID,
    payload: InventoryItemUpdate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("inventory.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> InventoryItemRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    item = await service.update_inventory_item(
        db,
        tenant_id=tid,
        business_id=business_id,
        location_id=location_id,
        inventory_item_id=inventory_item_id,
        payload=payload,
    )
    return InventoryItemRead.model_validate(item)


@router.post(
    "/businesses/{business_id}/locations/{location_id}/inventory-items/{inventory_item_id}/adjust",
    response_model=InventoryItemRead,
)
async def adjust_stock(
    business_id: uuid.UUID,
    location_id: uuid.UUID,
    inventory_item_id: uuid.UUID,
    payload: StockAdjust,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("inventory.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> InventoryItemRead:
    tid = _require_tenant(tenant_id)
    item = await service.adjust_stock(
        db,
        tenant_id=tid,
        business_id=business_id,
        location_id=location_id,
        inventory_item_id=inventory_item_id,
        payload=payload,
        actor_user_id=ctx.user.id,
    )
    return InventoryItemRead.model_validate(item)


@router.post(
    "/businesses/{business_id}/locations/{location_id}/inventory-items/{inventory_item_id}/reserve",
    response_model=InventoryItemRead,
)
async def reserve_stock(
    business_id: uuid.UUID,
    location_id: uuid.UUID,
    inventory_item_id: uuid.UUID,
    payload: StockQuantity,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("inventory.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> InventoryItemRead:
    tid = _require_tenant(tenant_id)
    item = await service.reserve_stock(
        db,
        tenant_id=tid,
        business_id=business_id,
        location_id=location_id,
        inventory_item_id=inventory_item_id,
        payload=payload,
        actor_user_id=ctx.user.id,
    )
    return InventoryItemRead.model_validate(item)


@router.post(
    "/businesses/{business_id}/locations/{location_id}/inventory-items/{inventory_item_id}/release",
    response_model=InventoryItemRead,
)
async def release_stock(
    business_id: uuid.UUID,
    location_id: uuid.UUID,
    inventory_item_id: uuid.UUID,
    payload: StockQuantity,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("inventory.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> InventoryItemRead:
    tid = _require_tenant(tenant_id)
    item = await service.release_stock(
        db,
        tenant_id=tid,
        business_id=business_id,
        location_id=location_id,
        inventory_item_id=inventory_item_id,
        payload=payload,
        actor_user_id=ctx.user.id,
    )
    return InventoryItemRead.model_validate(item)


@router.get(
    "/businesses/{business_id}/locations/{location_id}/inventory-items/{inventory_item_id}/movements",
    response_model=list[StockMovementRead],
)
async def list_stock_movements(
    business_id: uuid.UUID,
    location_id: uuid.UUID,
    inventory_item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("inventory.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[StockMovementRead]:
    _ = ctx
    tid = _require_tenant(tenant_id)
    rows = await service.list_stock_movements(
        db,
        tenant_id=tid,
        business_id=business_id,
        location_id=location_id,
        inventory_item_id=inventory_item_id,
    )
    return [StockMovementRead.model_validate(r) for r in rows]


@router.get(
    "/businesses/{business_id}/inventory/low-stock",
    response_model=list[InventoryItemRead],
)
async def list_low_stock(
    business_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("inventory.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[InventoryItemRead]:
    _ = ctx
    tid = _require_tenant(tenant_id)
    rows = await service.list_low_stock_items(
        db, tenant_id=tid, business_id=business_id
    )
    return [InventoryItemRead.model_validate(r) for r in rows]
