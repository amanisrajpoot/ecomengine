"""Auto-dispatch: create delivery and assign nearest online rider."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.events import event_bus
from app.delivery import service as delivery_service
from app.delivery.schemas import AssignDeliveryBody, DeliveryCreateBody
from app.fulfillment.service import get_by_order
from app.orders.service import get_order

logger = logging.getLogger(__name__)

DISPATCH_PROFILES = frozenset({"FOOD_DELIVERY", "HYPERLOCAL_DELIVERY", "COURIER"})
SKIP_FULFILLMENT_TYPES = frozenset({"SELF_PICKUP"})


async def auto_dispatch_order(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    order_id: uuid.UUID,
) -> dict[str, str | None]:
    """Idempotent create + assign for food, hyperlocal, and courier orders."""
    order, _items, _events = await get_order(db, tenant_id=tenant_id, order_id=order_id)

    if order.state_machine_profile not in DISPATCH_PROFILES:
        return {"status": "skipped", "reason": "profile"}
    if order.fulfillment_type in SKIP_FULFILLMENT_TYPES:
        return {"status": "skipped", "reason": "self_pickup"}

    if order.state_machine_profile == "COURIER":
        if order.status not in {"PAYMENT_CONFIRMED", "PICKUP_ASSIGNED"}:
            return {"status": "skipped", "reason": "order_status"}
    elif order.status not in {"READY", "PICKED_UP", "OUT_FOR_DELIVERY"}:
        return {"status": "skipped", "reason": "order_status"}

    graph = await get_by_order(db, tenant_id=tenant_id, order_id=order_id)
    if not graph:
        return {"status": "failed", "reason": "no_fulfillment"}
    fulfillment, _ = graph
    if fulfillment.type in SKIP_FULFILLMENT_TYPES:
        return {"status": "skipped", "reason": "self_pickup"}

    try:
        delivery_graph = await delivery_service.get_by_fulfillment(
            db, tenant_id=tenant_id, fulfillment_id=fulfillment.id
        )
        delivery = delivery_graph[0] if delivery_graph else None

        if not delivery:
            delivery, _ = await delivery_service.create_delivery_for_fulfillment(
                db,
                tenant_id=tenant_id,
                fulfillment_id=fulfillment.id,
                payload=DeliveryCreateBody(),
            )

        if delivery.partner_id and delivery.status not in {"CREATED", "CANCELLED", "FAILED"}:
            return {
                "status": "assigned",
                "delivery_id": str(delivery.id),
                "partner_id": str(delivery.partner_id),
            }

        if delivery.status in {"CREATED", "OFFERED"}:
            delivery, _ = await delivery_service.assign_delivery(
                db,
                tenant_id=tenant_id,
                delivery_id=delivery.id,
                payload=AssignDeliveryBody(),
            )

        if delivery.partner_id:
            return {
                "status": "assigned",
                "delivery_id": str(delivery.id),
                "partner_id": str(delivery.partner_id),
            }

        return {"status": "pending", "delivery_id": str(delivery.id)}
    except AppError as exc:
        logger.info(
            "auto_dispatch failed order=%s code=%s",
            order_id,
            exc.code,
        )
        await event_bus.publish(
            "DispatchFailed",
            {
                "tenant_id": str(tenant_id),
                "order_id": str(order_id),
                "code": exc.code,
                "message": exc.message,
            },
        )
        return {"status": "failed", "reason": exc.code, "message": exc.message}
