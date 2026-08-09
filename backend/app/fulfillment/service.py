"""Fulfillment domain services — create from order, transition, sync."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.events import event_bus
from app.fulfillment.models import Fulfillment, FulfillmentStatusEvent
from app.fulfillment.schemas import FulfillmentCreateBody, FulfillmentTransitionRequest
from app.fulfillment.states import FULFILLMENT_TYPES, ORDER_TO_FULFILLMENT, registry
from app.orders.models import Order


async def _load_graph(
    db: AsyncSession, *, tenant_id: uuid.UUID, fulfillment_id: uuid.UUID
) -> tuple[Fulfillment, list[FulfillmentStatusEvent]]:
    fulfillment = await db.scalar(
        select(Fulfillment).where(
            Fulfillment.id == fulfillment_id, Fulfillment.tenant_id == tenant_id
        )
    )
    if not fulfillment:
        raise AppError("FULFILLMENT_NOT_FOUND", "Fulfillment not found", 404)
    events = list(
        await db.scalars(
            select(FulfillmentStatusEvent)
            .where(FulfillmentStatusEvent.fulfillment_id == fulfillment.id)
            .order_by(FulfillmentStatusEvent.created_at.asc())
        )
    )
    return fulfillment, events


async def get_by_order(
    db: AsyncSession, *, tenant_id: uuid.UUID, order_id: uuid.UUID
) -> tuple[Fulfillment, list[FulfillmentStatusEvent]] | None:
    fulfillment = await db.scalar(
        select(Fulfillment).where(
            Fulfillment.tenant_id == tenant_id, Fulfillment.order_id == order_id
        )
    )
    if not fulfillment:
        return None
    return await _load_graph(db, tenant_id=tenant_id, fulfillment_id=fulfillment.id)


async def get_fulfillment(
    db: AsyncSession, *, tenant_id: uuid.UUID, fulfillment_id: uuid.UUID
) -> tuple[Fulfillment, list[FulfillmentStatusEvent]]:
    return await _load_graph(db, tenant_id=tenant_id, fulfillment_id=fulfillment_id)


async def list_fulfillments(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    status: str | None = None,
    fulfillment_type: str | None = None,
    order_id: uuid.UUID | None = None,
) -> list[Fulfillment]:
    stmt = select(Fulfillment).where(Fulfillment.tenant_id == tenant_id)
    if status:
        stmt = stmt.where(Fulfillment.status == status)
    if fulfillment_type:
        stmt = stmt.where(Fulfillment.type == fulfillment_type)
    if order_id:
        stmt = stmt.where(Fulfillment.order_id == order_id)
    stmt = stmt.order_by(Fulfillment.created_at.desc())
    return list(await db.scalars(stmt))


async def ensure_fulfillment_for_order(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    order: Order,
    payload: FulfillmentCreateBody | None = None,
    actor_user_id: uuid.UUID | None = None,
    commit: bool = True,
) -> Fulfillment:
    """Idempotent: one fulfillment per order. Created at payment confirmation."""
    existing = await db.scalar(
        select(Fulfillment).where(
            Fulfillment.tenant_id == tenant_id, Fulfillment.order_id == order.id
        )
    )
    if existing:
        return existing

    ftype = (payload.type if payload and payload.type else None) or order.fulfillment_type
    if ftype not in FULFILLMENT_TYPES:
        raise AppError(
            "INVALID_FULFILLMENT_TYPE",
            f"Unsupported fulfillment type: {ftype}",
            400,
            details={"allowed": sorted(FULFILLMENT_TYPES)},
        )

    meta = {
        "business_id": str(order.business_id) if order.business_id else None,
        "location_id": str(order.location_id) if order.location_id else None,
        "state_machine_profile": order.state_machine_profile,
        **(payload.metadata if payload else {}),
    }
    order_meta = order.metadata_json if isinstance(order.metadata_json, dict) else {}
    if "pickup" in order_meta and "pickup" not in meta:
        meta["pickup"] = order_meta["pickup"]
    if "drop" in order_meta:
        meta.setdefault("dropoff", order_meta["drop"])
        meta.setdefault("drop", order_meta["drop"])
    if "package" in order_meta and "package" not in meta:
        meta["package"] = order_meta["package"]
    fulfillment = Fulfillment(
        tenant_id=tenant_id,
        order_id=order.id,
        type=ftype,
        status="PENDING",
        scheduled_for=payload.scheduled_for if payload else None,
        metadata_json=meta,
    )
    db.add(fulfillment)
    await db.flush()
    db.add(
        FulfillmentStatusEvent(
            fulfillment_id=fulfillment.id,
            from_status=None,
            to_status="PENDING",
            actor_user_id=actor_user_id,
            actor_role="system",
            reason="created_from_order",
        )
    )
    if commit:
        await db.commit()
        await db.refresh(fulfillment)
    else:
        await db.flush()

    await event_bus.publish(
        "FulfillmentCreated",
        {
            "tenant_id": str(tenant_id),
            "fulfillment_id": str(fulfillment.id),
            "order_id": str(order.id),
            "type": fulfillment.type,
            "status": fulfillment.status,
        },
    )
    return fulfillment


async def create_for_order(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    order_id: uuid.UUID,
    payload: FulfillmentCreateBody,
    actor_user_id: uuid.UUID | None,
) -> tuple[Fulfillment, list[FulfillmentStatusEvent]]:
    order = await db.scalar(
        select(Order).where(Order.id == order_id, Order.tenant_id == tenant_id)
    )
    if not order:
        raise AppError("ORDER_NOT_FOUND", "Order not found", 404)
    if order.status in {"CREATED", "PAYMENT_PENDING"}:
        raise AppError(
            "ORDER_NOT_READY_FOR_FULFILLMENT",
            "Fulfillment requires payment confirmation",
            409,
        )
    fulfillment = await ensure_fulfillment_for_order(
        db,
        tenant_id=tenant_id,
        order=order,
        payload=payload,
        actor_user_id=actor_user_id,
        commit=True,
    )
    return await _load_graph(db, tenant_id=tenant_id, fulfillment_id=fulfillment.id)


async def transition_fulfillment(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    fulfillment_id: uuid.UUID,
    payload: FulfillmentTransitionRequest,
    actor_user_id: uuid.UUID | None,
) -> tuple[Fulfillment, list[FulfillmentStatusEvent]]:
    fulfillment, _events = await _load_graph(
        db, tenant_id=tenant_id, fulfillment_id=fulfillment_id
    )
    registry.assert_can_transition(
        fulfillment.status, payload.to_status, payload.actor, fulfillment.type
    )
    previous = fulfillment.status
    fulfillment.status = payload.to_status
    db.add(
        FulfillmentStatusEvent(
            fulfillment_id=fulfillment.id,
            from_status=previous,
            to_status=payload.to_status,
            actor_user_id=actor_user_id,
            actor_role=payload.actor,
            reason=payload.reason,
        )
    )
    await db.commit()
    await db.refresh(fulfillment)
    await event_bus.publish(
        "FulfillmentStatusChanged",
        {
            "tenant_id": str(tenant_id),
            "fulfillment_id": str(fulfillment.id),
            "order_id": str(fulfillment.order_id),
            "from_status": previous,
            "to_status": payload.to_status,
            "type": fulfillment.type,
        },
    )
    return await _load_graph(db, tenant_id=tenant_id, fulfillment_id=fulfillment.id)


async def sync_from_order_status(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    order: Order,
    actor_user_id: uuid.UUID | None = None,
) -> Fulfillment | None:
    """Advance or create fulfillment when the order status changes.

    Uses the fulfillment state machine; skips if target is unreachable or already there.
    """
    target = ORDER_TO_FULFILLMENT.get(order.status)
    if not target:
        return None

    if order.status == "PAYMENT_CONFIRMED" or target == "PENDING":
        fulfillment = await ensure_fulfillment_for_order(
            db,
            tenant_id=tenant_id,
            order=order,
            actor_user_id=actor_user_id,
            commit=True,
        )
        if target == "PENDING":
            return fulfillment
    else:
        fulfillment = await db.scalar(
            select(Fulfillment).where(
                Fulfillment.tenant_id == tenant_id, Fulfillment.order_id == order.id
            )
        )
        if not fulfillment:
            fulfillment = await ensure_fulfillment_for_order(
                db,
                tenant_id=tenant_id,
                order=order,
                actor_user_id=actor_user_id,
                commit=True,
            )

    if fulfillment.status == target:
        return fulfillment

    # Walk allowed one-step if needed, or jump when actor=system is permitted.
    if registry.can_transition(fulfillment.status, target, "system", fulfillment.type):
        await transition_fulfillment(
            db,
            tenant_id=tenant_id,
            fulfillment_id=fulfillment.id,
            payload=FulfillmentTransitionRequest(
                to_status=target, actor="system", reason=f"sync_from_order:{order.status}"
            ),
            actor_user_id=actor_user_id,
        )
        return (await _load_graph(db, tenant_id=tenant_id, fulfillment_id=fulfillment.id))[0]

    # Multi-hop for common food path PENDING→ACCEPTED→… when order jumps ahead.
    path_hints = {
        ("PENDING", "READY"): ["ACCEPTED", "READY"],
        ("PENDING", "PREPARING"): ["ACCEPTED", "PREPARING"],
        ("PENDING", "AWAITING_PICKUP"): ["ACCEPTED", "READY", "AWAITING_PICKUP"],
        ("PENDING", "IN_TRANSIT"): ["ACCEPTED", "READY", "AWAITING_PICKUP", "IN_TRANSIT"],
        ("PENDING", "COMPLETED"): ["ACCEPTED", "READY", "COMPLETED"],
        ("ACCEPTED", "READY"): ["READY"],
        ("ACCEPTED", "AWAITING_PICKUP"): ["READY", "AWAITING_PICKUP"],
        ("ACCEPTED", "IN_TRANSIT"): ["READY", "AWAITING_PICKUP", "IN_TRANSIT"],
        ("ACCEPTED", "COMPLETED"): ["READY", "COMPLETED"],
        ("PREPARING", "AWAITING_PICKUP"): ["READY", "AWAITING_PICKUP"],
        ("PREPARING", "IN_TRANSIT"): ["READY", "AWAITING_PICKUP", "IN_TRANSIT"],
        ("PREPARING", "COMPLETED"): ["READY", "COMPLETED"],
        ("READY", "IN_TRANSIT"): ["AWAITING_PICKUP", "IN_TRANSIT"],
        ("READY", "COMPLETED"): ["COMPLETED"],
        ("AWAITING_PICKUP", "COMPLETED"): ["COMPLETED"],
    }
    hops = path_hints.get((fulfillment.status, target), [])
    for hop in hops:
        fulfillment, _ = await _load_graph(
            db, tenant_id=tenant_id, fulfillment_id=fulfillment.id
        )
        if fulfillment.status == hop:
            continue
        if not registry.can_transition(fulfillment.status, hop, "system", fulfillment.type):
            break
        await transition_fulfillment(
            db,
            tenant_id=tenant_id,
            fulfillment_id=fulfillment.id,
            payload=FulfillmentTransitionRequest(
                to_status=hop, actor="system", reason=f"sync_from_order:{order.status}"
            ),
            actor_user_id=actor_user_id,
        )
    return await db.scalar(
        select(Fulfillment).where(
            Fulfillment.tenant_id == tenant_id, Fulfillment.order_id == order.id
        )
    )
