"""Inventory services — all stock changes create StockMovement rows."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.businesses.service import get_business
from app.catalog.models import Variant
from app.core.errors import AppError
from app.inventory.models import InventoryItem, StockMovement
from app.inventory.schemas import (
    InventoryAdjust,
    InventoryConsume,
    InventoryItemUpsert,
    InventoryRelease,
    InventoryReserve,
    StockReason,
)
from app.locations.models import BusinessLocation


async def _require_inventory_capability(
    db: AsyncSession, *, tenant_id: uuid.UUID, business_id: uuid.UUID
) -> None:
    business = await get_business(db, tenant_id=tenant_id, business_id=business_id)
    if not business.capabilities.get("inventory", False):
        raise AppError(
            "INVENTORY_DISABLED",
            "Inventory capability is not enabled for this business",
            status_code=409,
        )


async def _get_item(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    item_id: uuid.UUID,
) -> InventoryItem:
    item = await db.scalar(
        select(InventoryItem).where(
            InventoryItem.id == item_id,
            InventoryItem.tenant_id == tenant_id,
            InventoryItem.business_id == business_id,
        )
    )
    if not item:
        raise AppError("INVENTORY_NOT_FOUND", "Inventory item not found", 404)
    return item


async def _apply_movement(
    db: AsyncSession,
    *,
    item: InventoryItem,
    reason: str,
    delta_on_hand: int,
    delta_reserved: int,
    created_by: uuid.UUID | None,
    reference_type: str | None = None,
    reference_id: uuid.UUID | None = None,
    note: str | None = None,
    commit: bool = True,
) -> tuple[InventoryItem, StockMovement]:
    new_on_hand = item.on_hand + delta_on_hand
    new_reserved = item.reserved + delta_reserved
    if new_on_hand < 0 or new_reserved < 0 or new_on_hand < new_reserved:
        raise AppError(
            "INSUFFICIENT_STOCK",
            "Stock movement would violate on_hand/reserved invariants",
            status_code=409,
            details={
                "on_hand": item.on_hand,
                "reserved": item.reserved,
                "delta_on_hand": delta_on_hand,
                "delta_reserved": delta_reserved,
            },
        )

    movement = StockMovement(
        tenant_id=item.tenant_id,
        inventory_item_id=item.id,
        reason=reason,
        delta_on_hand=delta_on_hand,
        delta_reserved=delta_reserved,
        reference_type=reference_type,
        reference_id=reference_id,
        created_by=created_by,
        note=note,
    )
    item.on_hand = new_on_hand
    item.reserved = new_reserved
    db.add(movement)
    if commit:
        await db.commit()
        await db.refresh(item)
        await db.refresh(movement)
    else:
        await db.flush()
    return item, movement


async def upsert_inventory_item(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    payload: InventoryItemUpsert,
) -> InventoryItem:
    await _require_inventory_capability(db, tenant_id=tenant_id, business_id=business_id)

    location = await db.scalar(
        select(BusinessLocation).where(
            BusinessLocation.id == payload.location_id,
            BusinessLocation.business_id == business_id,
            BusinessLocation.tenant_id == tenant_id,
        )
    )
    if not location:
        raise AppError("LOCATION_NOT_FOUND", "Business location not found", 404)

    variant = await db.scalar(
        select(Variant).where(Variant.id == payload.variant_id, Variant.tenant_id == tenant_id)
    )
    if not variant:
        raise AppError("VARIANT_NOT_FOUND", "Variant not found", 404)

    existing = await db.scalar(
        select(InventoryItem).where(
            InventoryItem.location_id == payload.location_id,
            InventoryItem.variant_id == payload.variant_id,
        )
    )
    if existing:
        if payload.low_stock_threshold is not None:
            existing.low_stock_threshold = payload.low_stock_threshold
            await db.commit()
            await db.refresh(existing)
        return existing

    item = InventoryItem(
        tenant_id=tenant_id,
        business_id=business_id,
        location_id=payload.location_id,
        variant_id=payload.variant_id,
        on_hand=0,
        reserved=0,
        low_stock_threshold=payload.low_stock_threshold,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def list_inventory(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    location_id: uuid.UUID | None = None,
    low_stock_only: bool = False,
    out_of_stock_only: bool = False,
) -> list[InventoryItem]:
    await get_business(db, tenant_id=tenant_id, business_id=business_id)
    stmt = select(InventoryItem).where(
        InventoryItem.tenant_id == tenant_id,
        InventoryItem.business_id == business_id,
    )
    if location_id:
        stmt = stmt.where(InventoryItem.location_id == location_id)
    items = list(await db.scalars(stmt.order_by(InventoryItem.updated_at.desc())))
    if low_stock_only:
        items = [
            i
            for i in items
            if i.low_stock_threshold is not None
            and (i.on_hand - i.reserved) <= i.low_stock_threshold
        ]
    if out_of_stock_only:
        items = [i for i in items if (i.on_hand - i.reserved) <= 0]
    return items


async def get_inventory_item(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    item_id: uuid.UUID,
) -> InventoryItem:
    return await _get_item(db, tenant_id=tenant_id, business_id=business_id, item_id=item_id)


async def adjust_stock(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    item_id: uuid.UUID,
    payload: InventoryAdjust,
    actor_user_id: uuid.UUID | None,
) -> tuple[InventoryItem, StockMovement]:
    await _require_inventory_capability(db, tenant_id=tenant_id, business_id=business_id)
    if payload.delta_on_hand == 0:
        raise AppError("INVALID_ADJUSTMENT", "delta_on_hand must be non-zero", 400)
    reason = payload.reason.value
    if payload.delta_on_hand > 0 and payload.reason == StockReason.ADJUSTMENT:
        # Keep caller's reason; RECEIVE is preferred for inbound but ADJUSTMENT allowed.
        pass
    item = await _get_item(db, tenant_id=tenant_id, business_id=business_id, item_id=item_id)
    return await _apply_movement(
        db,
        item=item,
        reason=reason,
        delta_on_hand=payload.delta_on_hand,
        delta_reserved=0,
        created_by=actor_user_id,
        reference_type=payload.reference_type,
        reference_id=payload.reference_id,
        note=payload.note,
    )


async def reserve_stock(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    item_id: uuid.UUID,
    payload: InventoryReserve,
    actor_user_id: uuid.UUID | None,
) -> tuple[InventoryItem, StockMovement]:
    await _require_inventory_capability(db, tenant_id=tenant_id, business_id=business_id)
    item = await _get_item(db, tenant_id=tenant_id, business_id=business_id, item_id=item_id)
    return await _apply_movement(
        db,
        item=item,
        reason=StockReason.RESERVE.value,
        delta_on_hand=0,
        delta_reserved=payload.quantity,
        created_by=actor_user_id,
        reference_type=payload.reference_type,
        reference_id=payload.reference_id,
        note=payload.note,
    )


async def release_stock(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    item_id: uuid.UUID,
    payload: InventoryRelease,
    actor_user_id: uuid.UUID | None,
) -> tuple[InventoryItem, StockMovement]:
    await _require_inventory_capability(db, tenant_id=tenant_id, business_id=business_id)
    item = await _get_item(db, tenant_id=tenant_id, business_id=business_id, item_id=item_id)
    return await _apply_movement(
        db,
        item=item,
        reason=StockReason.RELEASE.value,
        delta_on_hand=0,
        delta_reserved=-payload.quantity,
        created_by=actor_user_id,
        reference_type=payload.reference_type,
        reference_id=payload.reference_id,
        note=payload.note,
    )


async def consume_stock(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    item_id: uuid.UUID,
    payload: InventoryConsume,
    actor_user_id: uuid.UUID | None,
) -> tuple[InventoryItem, StockMovement]:
    await _require_inventory_capability(db, tenant_id=tenant_id, business_id=business_id)
    item = await _get_item(db, tenant_id=tenant_id, business_id=business_id, item_id=item_id)
    return await _apply_movement(
        db,
        item=item,
        reason=StockReason.CONSUME.value,
        delta_on_hand=-payload.quantity,
        delta_reserved=-payload.quantity,
        created_by=actor_user_id,
        reference_type=payload.reference_type,
        reference_id=payload.reference_id,
        note=payload.note,
    )


async def list_movements(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    item_id: uuid.UUID,
) -> list[StockMovement]:
    await _get_item(db, tenant_id=tenant_id, business_id=business_id, item_id=item_id)
    stmt = (
        select(StockMovement)
        .where(
            StockMovement.tenant_id == tenant_id,
            StockMovement.inventory_item_id == item_id,
        )
        .order_by(StockMovement.created_at.desc())
    )
    return list(await db.scalars(stmt))


async def _item_for_variant_location(
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


async def reserve_for_order(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    order,
    items: list,
    actor_user_id: uuid.UUID | None,
    commit: bool = False,
) -> list[StockMovement]:
    """Reserve stock for each order line at payment confirmation (hyperlocal)."""
    from app.businesses.models import Business

    if not order.business_id or not order.location_id:
        return []
    business = await db.get(Business, order.business_id)
    if not business or not business.capabilities.get("inventory", False):
        return []

    movements: list[StockMovement] = []
    for line in items:
        if not line.variant_id or line.quantity <= 0:
            continue
        item = await _item_for_variant_location(
            db,
            tenant_id=tenant_id,
            business_id=order.business_id,
            location_id=order.location_id,
            variant_id=line.variant_id,
        )
        if not item:
            raise AppError(
                "INVENTORY_NOT_FOUND",
                f"No inventory for variant {line.variant_id} at order location",
                409,
                details={"variant_id": str(line.variant_id), "location_id": str(order.location_id)},
            )
        _item, movement = await _apply_movement(
            db,
            item=item,
            reason=StockReason.RESERVE.value,
            delta_on_hand=0,
            delta_reserved=line.quantity,
            created_by=actor_user_id,
            reference_type="order",
            reference_id=order.id,
            note="reserve_on_payment_confirmed",
            commit=commit,
        )
        movements.append(movement)
    return movements


async def consume_for_order(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    order,
    items: list,
    actor_user_id: uuid.UUID | None,
    commit: bool = False,
) -> list[StockMovement]:
    """Consume reserved stock when order is delivered."""
    from app.businesses.models import Business

    if not order.business_id or not order.location_id:
        return []
    business = await db.get(Business, order.business_id)
    if not business or not business.capabilities.get("inventory", False):
        return []

    movements: list[StockMovement] = []
    for line in items:
        if not line.variant_id or line.quantity <= 0:
            continue
        item = await _item_for_variant_location(
            db,
            tenant_id=tenant_id,
            business_id=order.business_id,
            location_id=order.location_id,
            variant_id=line.variant_id,
        )
        if not item:
            continue
        _item, movement = await _apply_movement(
            db,
            item=item,
            reason=StockReason.CONSUME.value,
            delta_on_hand=-line.quantity,
            delta_reserved=-line.quantity,
            created_by=actor_user_id,
            reference_type="order",
            reference_id=order.id,
            note="consume_on_delivered",
            commit=commit,
        )
        movements.append(movement)
    return movements


async def release_for_order(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    order,
    items: list,
    actor_user_id: uuid.UUID | None,
    commit: bool = False,
) -> list[StockMovement]:
    """Release reserved stock when a paid order is cancelled."""
    from app.businesses.models import Business

    if not order.business_id or not order.location_id:
        return []
    business = await db.get(Business, order.business_id)
    if not business or not business.capabilities.get("inventory", False):
        return []

    movements: list[StockMovement] = []
    for line in items:
        if not line.variant_id or line.quantity <= 0:
            continue
        item = await _item_for_variant_location(
            db,
            tenant_id=tenant_id,
            business_id=order.business_id,
            location_id=order.location_id,
            variant_id=line.variant_id,
        )
        if not item:
            continue
        # Only release what is still reserved for this line.
        qty = min(line.quantity, item.reserved)
        if qty <= 0:
            continue
        _item, movement = await _apply_movement(
            db,
            item=item,
            reason=StockReason.RELEASE.value,
            delta_on_hand=0,
            delta_reserved=-qty,
            created_by=actor_user_id,
            reference_type="order",
            reference_id=order.id,
            note="release_on_cancel",
            commit=commit,
        )
        movements.append(movement)
    return movements
