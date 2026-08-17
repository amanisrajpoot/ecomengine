"""Inventory hooks for order lifecycle (hyperlocal)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.businesses.service import get_business
from app.core.errors import AppError
from app.inventory.models import InventoryItem, StockMovement
from app.inventory.schemas import StockReason
from app.inventory.service import _record_movement, _validate_stock
from app.orders.models import Order


async def _inventory_item_for_variant(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    location_id: uuid.UUID,
    variant_id: uuid.UUID,
) -> InventoryItem | None:
    return await db.scalar(
        select(InventoryItem).where(
            InventoryItem.tenant_id == tenant_id,
            InventoryItem.business_id == business_id,
            InventoryItem.location_id == location_id,
            InventoryItem.variant_id == variant_id,
        )
    )


async def _has_movement(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    order_id: uuid.UUID,
    reason: str,
) -> bool:
    movement = await db.scalar(
        select(StockMovement.id).where(
            StockMovement.tenant_id == tenant_id,
            StockMovement.reference_type == "ORDER",
            StockMovement.reference_id == order_id,
            StockMovement.reason == reason,
        )
    )
    return movement is not None


async def _should_manage_inventory(db: AsyncSession, order: Order) -> bool:
    if order.state_machine_profile != "HYPERLOCAL_DELIVERY":
        return False
    if not order.business_id or not order.location_id:
        return False
    business = await get_business(
        db, tenant_id=order.tenant_id, business_id=order.business_id
    )
    return bool(business.capabilities.get("inventory", False))


async def reserve_inventory_for_order(
    db: AsyncSession,
    *,
    order: Order,
    actor_user_id: uuid.UUID | None = None,
) -> None:
    if not await _should_manage_inventory(db, order):
        return
    if await _has_movement(
        db, tenant_id=order.tenant_id, order_id=order.id, reason=StockReason.RESERVE.value
    ):
        return

    for line in order.items:
        if line.variant_id is None:
            continue
        item = await _inventory_item_for_variant(
            db,
            tenant_id=order.tenant_id,
            business_id=order.business_id,
            location_id=order.location_id,
            variant_id=line.variant_id,
        )
        if not item:
            raise AppError(
                "INVENTORY_NOT_FOUND",
                f"No inventory for variant {line.variant_id}",
                status_code=400,
            )
        available = item.on_hand - item.reserved
        if line.quantity > available:
            raise AppError(
                "INSUFFICIENT_STOCK",
                f"Cannot reserve {line.quantity}; only {available} available",
                status_code=400,
            )
        item.reserved += line.quantity
        _validate_stock(item)
        await _record_movement(
            db,
            tenant_id=order.tenant_id,
            inventory_item_id=item.id,
            reason=StockReason.RESERVE.value,
            delta_on_hand=0,
            delta_reserved=line.quantity,
            reference_type="ORDER",
            reference_id=order.id,
            created_by=actor_user_id,
        )


async def consume_inventory_for_order(
    db: AsyncSession,
    *,
    order: Order,
    actor_user_id: uuid.UUID | None = None,
) -> None:
    if not await _should_manage_inventory(db, order):
        return
    if await _has_movement(
        db, tenant_id=order.tenant_id, order_id=order.id, reason=StockReason.CONSUME.value
    ):
        return

    for line in order.items:
        if line.variant_id is None:
            continue
        item = await _inventory_item_for_variant(
            db,
            tenant_id=order.tenant_id,
            business_id=order.business_id,
            location_id=order.location_id,
            variant_id=line.variant_id,
        )
        if not item:
            continue
        qty = line.quantity
        if item.reserved < qty:
            raise AppError(
                "INVALID_CONSUME",
                f"Cannot consume {qty}; only {item.reserved} reserved",
                status_code=400,
            )
        item.on_hand -= qty
        item.reserved -= qty
        _validate_stock(item)
        await _record_movement(
            db,
            tenant_id=order.tenant_id,
            inventory_item_id=item.id,
            reason=StockReason.CONSUME.value,
            delta_on_hand=-qty,
            delta_reserved=-qty,
            reference_type="ORDER",
            reference_id=order.id,
            created_by=actor_user_id,
        )


async def release_inventory_for_order(
    db: AsyncSession,
    *,
    order: Order,
    actor_user_id: uuid.UUID | None = None,
) -> None:
    if not await _should_manage_inventory(db, order):
        return
    if await _has_movement(
        db, tenant_id=order.tenant_id, order_id=order.id, reason=StockReason.CONSUME.value
    ):
        return
    if await _has_movement(
        db, tenant_id=order.tenant_id, order_id=order.id, reason=StockReason.RELEASE.value
    ):
        return
    if not await _has_movement(
        db, tenant_id=order.tenant_id, order_id=order.id, reason=StockReason.RESERVE.value
    ):
        return

    for line in order.items:
        if line.variant_id is None:
            continue
        item = await _inventory_item_for_variant(
            db,
            tenant_id=order.tenant_id,
            business_id=order.business_id,
            location_id=order.location_id,
            variant_id=line.variant_id,
        )
        if not item or item.reserved < line.quantity:
            continue
        qty = line.quantity
        item.reserved -= qty
        _validate_stock(item)
        await _record_movement(
            db,
            tenant_id=order.tenant_id,
            inventory_item_id=item.id,
            reason=StockReason.RELEASE.value,
            delta_on_hand=0,
            delta_reserved=-qty,
            reference_type="ORDER",
            reference_id=order.id,
            created_by=actor_user_id,
        )
