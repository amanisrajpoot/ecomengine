"""Fulfillment creation and lifecycle."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.fulfillment.models import Fulfillment
from app.fulfillment.schemas import FulfillmentTransition
from app.fulfillment.states import FULFILLMENT_TYPES, can_transition
from app.orders.models import Order


async def _get_fulfillment(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    fulfillment_id: uuid.UUID,
) -> Fulfillment:
    fulfillment = await db.scalar(
        select(Fulfillment).where(
            Fulfillment.id == fulfillment_id,
            Fulfillment.tenant_id == tenant_id,
        )
    )
    if not fulfillment:
        raise AppError("FULFILLMENT_NOT_FOUND", "Fulfillment not found", status_code=404)
    return fulfillment


async def create_for_order(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    order_id: uuid.UUID,
    fulfillment_type: str,
    scheduled_for: datetime | None = None,
) -> Fulfillment:
    if fulfillment_type not in FULFILLMENT_TYPES:
        raise AppError(
            "INVALID_FULFILLMENT_TYPE",
            f"type must be one of {sorted(FULFILLMENT_TYPES)}",
            status_code=400,
        )

    existing = await db.scalar(
        select(Fulfillment).where(Fulfillment.order_id == order_id)
    )
    if existing:
        return existing

    fulfillment = Fulfillment(
        tenant_id=tenant_id,
        order_id=order_id,
        type=fulfillment_type,
        status="PENDING",
        scheduled_for=scheduled_for,
    )
    db.add(fulfillment)
    await db.flush()
    return fulfillment


async def get_fulfillment_for_order(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    order_id: uuid.UUID,
) -> Fulfillment:
    fulfillment = await db.scalar(
        select(Fulfillment).where(
            Fulfillment.tenant_id == tenant_id,
            Fulfillment.order_id == order_id,
        )
    )
    if not fulfillment:
        raise AppError(
            "FULFILLMENT_NOT_FOUND",
            "Fulfillment not found for order",
            status_code=404,
        )
    return fulfillment


async def get_fulfillment(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    fulfillment_id: uuid.UUID,
) -> Fulfillment:
    return await _get_fulfillment(db, tenant_id=tenant_id, fulfillment_id=fulfillment_id)


async def list_fulfillments(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    status: str | None = None,
    fulfillment_type: str | None = None,
    business_id: uuid.UUID | None = None,
) -> list[Fulfillment]:
    stmt = select(Fulfillment).where(Fulfillment.tenant_id == tenant_id)
    if status:
        stmt = stmt.where(Fulfillment.status == status)
    if fulfillment_type:
        stmt = stmt.where(Fulfillment.type == fulfillment_type)
    if business_id:
        stmt = stmt.join(Order, Fulfillment.order_id == Order.id).where(
            Order.business_id == business_id
        )
    stmt = stmt.order_by(Fulfillment.created_at.desc())
    return list(await db.scalars(stmt))


async def transition_fulfillment(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    fulfillment_id: uuid.UUID,
    payload: FulfillmentTransition,
    actor_user_id: uuid.UUID | None = None,
) -> Fulfillment:
    _ = actor_user_id
    fulfillment = await _get_fulfillment(db, tenant_id=tenant_id, fulfillment_id=fulfillment_id)
    if not can_transition(fulfillment.status, payload.to_status):
        raise AppError(
            "INVALID_FULFILLMENT_TRANSITION",
            f"Cannot transition from {fulfillment.status} to {payload.to_status}",
            status_code=400,
        )

    fulfillment.status = payload.to_status
    if payload.scheduled_for is not None:
        fulfillment.scheduled_for = payload.scheduled_for
    if payload.reason:
        fulfillment.meta = {
            **fulfillment.meta,
            "last_transition": {
                "to_status": payload.to_status,
                "reason": payload.reason,
            },
        }

    await db.commit()
    await db.refresh(fulfillment)
    return fulfillment
