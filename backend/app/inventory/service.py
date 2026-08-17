"""Inventory stock management."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.businesses.models import Business
from app.businesses.service import get_business
from app.catalog.models import Variant
from app.catalog.service import get_product
from app.core.errors import AppError
from app.inventory.models import InventoryItem, StockMovement
from app.inventory.schemas import (
    InventoryItemCreate,
    InventoryItemUpdate,
    StockAdjust,
    StockQuantity,
    StockReason,
)
from app.locations.service import get_location


async def _ensure_inventory_enabled(
    db: AsyncSession, *, tenant_id: uuid.UUID, business_id: uuid.UUID
) -> Business:
    business = await get_business(db, tenant_id=tenant_id, business_id=business_id)
    if not business.capabilities.get("inventory", False):
        raise AppError(
            "INVENTORY_NOT_ENABLED",
            "Inventory is not enabled for this business",
            status_code=400,
        )
    return business


async def _get_inventory_item(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    location_id: uuid.UUID,
    inventory_item_id: uuid.UUID,
) -> InventoryItem:
    item = await db.scalar(
        select(InventoryItem).where(
            InventoryItem.id == inventory_item_id,
            InventoryItem.tenant_id == tenant_id,
            InventoryItem.business_id == business_id,
            InventoryItem.location_id == location_id,
        )
    )
    if not item:
        raise AppError("INVENTORY_NOT_FOUND", "Inventory item not found", status_code=404)
    return item


async def _record_movement(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    inventory_item_id: uuid.UUID,
    reason: str,
    delta_on_hand: int,
    delta_reserved: int,
    reference_type: str | None = None,
    reference_id: uuid.UUID | None = None,
    created_by: uuid.UUID | None = None,
) -> StockMovement:
    movement = StockMovement(
        tenant_id=tenant_id,
        inventory_item_id=inventory_item_id,
        reason=reason,
        delta_on_hand=delta_on_hand,
        delta_reserved=delta_reserved,
        reference_type=reference_type,
        reference_id=reference_id,
        created_by=created_by,
    )
    db.add(movement)
    return movement


def _validate_stock(item: InventoryItem) -> None:
    if item.on_hand < 0 or item.reserved < 0 or item.on_hand < item.reserved:
        raise AppError(
            "INVALID_STOCK_STATE",
            "Stock levels must satisfy on_hand >= reserved >= 0",
            status_code=400,
        )


async def create_inventory_item(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    location_id: uuid.UUID,
    payload: InventoryItemCreate,
    actor_user_id: uuid.UUID | None = None,
) -> InventoryItem:
    await _ensure_inventory_enabled(db, tenant_id=tenant_id, business_id=business_id)
    await get_location(db, tenant_id=tenant_id, business_id=business_id, location_id=location_id)

    variant = await db.scalar(
        select(Variant).where(
            Variant.id == payload.variant_id,
            Variant.tenant_id == tenant_id,
        )
    )
    if not variant:
        raise AppError("VARIANT_NOT_FOUND", "Variant not found", status_code=404)

    await get_product(
        db,
        tenant_id=tenant_id,
        business_id=business_id,
        product_id=variant.product_id,
    )

    existing = await db.scalar(
        select(InventoryItem).where(
            InventoryItem.location_id == location_id,
            InventoryItem.variant_id == payload.variant_id,
        )
    )
    if existing:
        raise AppError(
            "INVENTORY_ALREADY_EXISTS",
            "Inventory item already exists for this location and variant",
            status_code=409,
        )

    if payload.on_hand < payload.reserved:
        raise AppError(
            "INVALID_STOCK_STATE",
            "on_hand must be >= reserved",
            status_code=400,
        )

    item = InventoryItem(
        tenant_id=tenant_id,
        business_id=business_id,
        location_id=location_id,
        variant_id=payload.variant_id,
        on_hand=payload.on_hand,
        reserved=payload.reserved,
        low_stock_threshold=payload.low_stock_threshold,
    )
    db.add(item)
    await db.flush()

    if payload.on_hand > 0 or payload.reserved > 0:
        await _record_movement(
            db,
            tenant_id=tenant_id,
            inventory_item_id=item.id,
            reason=StockReason.RECEIVE.value,
            delta_on_hand=payload.on_hand,
            delta_reserved=payload.reserved,
            created_by=actor_user_id,
        )

    await db.commit()
    await db.refresh(item)
    return item


async def list_inventory_items(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    location_id: uuid.UUID,
) -> list[InventoryItem]:
    await _ensure_inventory_enabled(db, tenant_id=tenant_id, business_id=business_id)
    await get_location(db, tenant_id=tenant_id, business_id=business_id, location_id=location_id)
    stmt = select(InventoryItem).where(
        InventoryItem.tenant_id == tenant_id,
        InventoryItem.business_id == business_id,
        InventoryItem.location_id == location_id,
    )
    stmt = stmt.order_by(InventoryItem.updated_at.desc())
    return list(await db.scalars(stmt))


async def get_inventory_item(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    location_id: uuid.UUID,
    inventory_item_id: uuid.UUID,
) -> InventoryItem:
    await _ensure_inventory_enabled(db, tenant_id=tenant_id, business_id=business_id)
    return await _get_inventory_item(
        db,
        tenant_id=tenant_id,
        business_id=business_id,
        location_id=location_id,
        inventory_item_id=inventory_item_id,
    )


async def update_inventory_item(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    location_id: uuid.UUID,
    inventory_item_id: uuid.UUID,
    payload: InventoryItemUpdate,
) -> InventoryItem:
    item = await _get_inventory_item(
        db,
        tenant_id=tenant_id,
        business_id=business_id,
        location_id=location_id,
        inventory_item_id=inventory_item_id,
    )
    await _ensure_inventory_enabled(db, tenant_id=tenant_id, business_id=business_id)
    if payload.low_stock_threshold is not None:
        item.low_stock_threshold = payload.low_stock_threshold
    await db.commit()
    await db.refresh(item)
    return item


async def adjust_stock(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    location_id: uuid.UUID,
    inventory_item_id: uuid.UUID,
    payload: StockAdjust,
    actor_user_id: uuid.UUID | None = None,
) -> InventoryItem:
    await _ensure_inventory_enabled(db, tenant_id=tenant_id, business_id=business_id)
    item = await _get_inventory_item(
        db,
        tenant_id=tenant_id,
        business_id=business_id,
        location_id=location_id,
        inventory_item_id=inventory_item_id,
    )
    item.on_hand += payload.delta_on_hand
    item.reserved += payload.delta_reserved
    _validate_stock(item)
    await _record_movement(
        db,
        tenant_id=tenant_id,
        inventory_item_id=item.id,
        reason=payload.reason.value,
        delta_on_hand=payload.delta_on_hand,
        delta_reserved=payload.delta_reserved,
        reference_type=payload.reference_type,
        reference_id=payload.reference_id,
        created_by=actor_user_id,
    )
    await db.commit()
    await db.refresh(item)
    return item


async def reserve_stock(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    location_id: uuid.UUID,
    inventory_item_id: uuid.UUID,
    payload: StockQuantity,
    actor_user_id: uuid.UUID | None = None,
) -> InventoryItem:
    await _ensure_inventory_enabled(db, tenant_id=tenant_id, business_id=business_id)
    item = await _get_inventory_item(
        db,
        tenant_id=tenant_id,
        business_id=business_id,
        location_id=location_id,
        inventory_item_id=inventory_item_id,
    )
    available = item.on_hand - item.reserved
    if payload.quantity > available:
        raise AppError(
            "INSUFFICIENT_STOCK",
            f"Cannot reserve {payload.quantity}; only {available} available",
            status_code=400,
        )
    item.reserved += payload.quantity
    _validate_stock(item)
    reason = payload.reason or StockReason.RESERVE
    await _record_movement(
        db,
        tenant_id=tenant_id,
        inventory_item_id=item.id,
        reason=reason.value,
        delta_on_hand=0,
        delta_reserved=payload.quantity,
        reference_type=payload.reference_type,
        reference_id=payload.reference_id,
        created_by=actor_user_id,
    )
    await db.commit()
    await db.refresh(item)
    return item


async def release_stock(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    location_id: uuid.UUID,
    inventory_item_id: uuid.UUID,
    payload: StockQuantity,
    actor_user_id: uuid.UUID | None = None,
) -> InventoryItem:
    await _ensure_inventory_enabled(db, tenant_id=tenant_id, business_id=business_id)
    item = await _get_inventory_item(
        db,
        tenant_id=tenant_id,
        business_id=business_id,
        location_id=location_id,
        inventory_item_id=inventory_item_id,
    )
    if payload.quantity > item.reserved:
        raise AppError(
            "INVALID_RELEASE",
            f"Cannot release {payload.quantity}; only {item.reserved} reserved",
            status_code=400,
        )
    item.reserved -= payload.quantity
    _validate_stock(item)
    reason = payload.reason or StockReason.RELEASE
    await _record_movement(
        db,
        tenant_id=tenant_id,
        inventory_item_id=item.id,
        reason=reason.value,
        delta_on_hand=0,
        delta_reserved=-payload.quantity,
        reference_type=payload.reference_type,
        reference_id=payload.reference_id,
        created_by=actor_user_id,
    )
    await db.commit()
    await db.refresh(item)
    return item


async def list_stock_movements(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    location_id: uuid.UUID,
    inventory_item_id: uuid.UUID,
) -> list[StockMovement]:
    await _ensure_inventory_enabled(db, tenant_id=tenant_id, business_id=business_id)
    await _get_inventory_item(
        db,
        tenant_id=tenant_id,
        business_id=business_id,
        location_id=location_id,
        inventory_item_id=inventory_item_id,
    )
    stmt = (
        select(StockMovement)
        .where(
            StockMovement.tenant_id == tenant_id,
            StockMovement.inventory_item_id == inventory_item_id,
        )
        .order_by(StockMovement.created_at.desc())
    )
    return list(await db.scalars(stmt))


async def list_low_stock_items(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
) -> list[InventoryItem]:
    await _ensure_inventory_enabled(db, tenant_id=tenant_id, business_id=business_id)
    items = list(
        await db.scalars(
            select(InventoryItem).where(
                InventoryItem.tenant_id == tenant_id,
                InventoryItem.business_id == business_id,
            )
        )
    )
    low: list[InventoryItem] = []
    for item in items:
        if item.low_stock_threshold is not None and item.on_hand <= item.low_stock_threshold:
            low.append(item)
    return low
