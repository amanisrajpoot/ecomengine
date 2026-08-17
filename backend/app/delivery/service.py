"""Delivery creation, assignment, and stop completion."""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import AppError
from app.delivery.models import Delivery, DeliveryStop
from app.delivery.schemas import DeliveryAssign, DeliveryCreate, StopComplete
from app.delivery.states import STOP_TYPES
from app.fulfillment.models import Fulfillment
from app.partners import service as partners_service
from app.partners.models import DeliveryPartnerProfile


def _distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


async def _get_delivery(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    delivery_id: uuid.UUID,
) -> Delivery:
    delivery = await db.scalar(
        select(Delivery)
        .options(selectinload(Delivery.stops))
        .where(Delivery.id == delivery_id, Delivery.tenant_id == tenant_id)
    )
    if not delivery:
        raise AppError("DELIVERY_NOT_FOUND", "Delivery not found", status_code=404)
    return delivery


async def _pickup_stop(stops: list[DeliveryStop]) -> DeliveryStop:
    pickup_stops = [s for s in stops if s.stop_type == "PICKUP"]
    if not pickup_stops:
        raise AppError("DELIVERY_NO_PICKUP", "Delivery has no pickup stop", status_code=400)
    return min(pickup_stops, key=lambda s: s.sequence)


async def _find_nearest_partner(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    pickup_lat: float,
    pickup_lng: float,
) -> DeliveryPartnerProfile | None:
    partners = await partners_service.list_available_partners(
        db, tenant_id=tenant_id, online_only=True
    )
    ranked = [
        p
        for p in partners
        if p.current_lat is not None and p.current_lng is not None
    ]
    if not ranked:
        return None
    ranked.sort(
        key=lambda p: _distance_km(pickup_lat, pickup_lng, p.current_lat, p.current_lng)
    )
    return ranked[0]


async def create_delivery_for_fulfillment(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    fulfillment_id: uuid.UUID,
    payload: DeliveryCreate,
) -> Delivery:
    fulfillment = await db.scalar(
        select(Fulfillment).where(
            Fulfillment.id == fulfillment_id,
            Fulfillment.tenant_id == tenant_id,
        )
    )
    if not fulfillment:
        raise AppError("FULFILLMENT_NOT_FOUND", "Fulfillment not found", status_code=404)

    existing = await db.scalar(
        select(Delivery).where(Delivery.fulfillment_id == fulfillment_id)
    )
    if existing:
        raise AppError("DELIVERY_ALREADY_EXISTS", "Delivery already exists for fulfillment", 400)

    for stop in payload.stops:
        if stop.stop_type not in STOP_TYPES:
            raise AppError(
                "INVALID_STOP_TYPE",
                f"stop_type must be one of {sorted(STOP_TYPES)}",
                status_code=400,
            )

    delivery = Delivery(
        tenant_id=tenant_id,
        fulfillment_id=fulfillment_id,
        status="PENDING",
    )
    db.add(delivery)
    await db.flush()

    for stop in sorted(payload.stops, key=lambda s: s.sequence):
        db.add(
            DeliveryStop(
                delivery_id=delivery.id,
                sequence=stop.sequence,
                stop_type=stop.stop_type,
                address=stop.address,
                lat=stop.lat,
                lng=stop.lng,
                contact=stop.contact,
            )
        )
    await db.flush()

    if payload.auto_assign:
        delivery = await _get_delivery(db, tenant_id=tenant_id, delivery_id=delivery.id)
        pickup = await _pickup_stop(delivery.stops)
        partner = await _find_nearest_partner(
            db,
            tenant_id=tenant_id,
            pickup_lat=pickup.lat,
            pickup_lng=pickup.lng,
        )
        if partner:
            delivery.partner_id = partner.id
            delivery.status = "ASSIGNED"

    await db.commit()
    return await _get_delivery(db, tenant_id=tenant_id, delivery_id=delivery.id)


async def get_delivery(
    db: AsyncSession, *, tenant_id: uuid.UUID, delivery_id: uuid.UUID
) -> Delivery:
    return await _get_delivery(db, tenant_id=tenant_id, delivery_id=delivery_id)


async def get_delivery_for_fulfillment(
    db: AsyncSession, *, tenant_id: uuid.UUID, fulfillment_id: uuid.UUID
) -> Delivery:
    delivery = await db.scalar(
        select(Delivery)
        .options(selectinload(Delivery.stops))
        .where(
            Delivery.tenant_id == tenant_id,
            Delivery.fulfillment_id == fulfillment_id,
        )
    )
    if not delivery:
        raise AppError(
            "DELIVERY_NOT_FOUND",
            "Delivery not found for fulfillment",
            status_code=404,
        )
    return delivery


async def assign_delivery(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    delivery_id: uuid.UUID,
    payload: DeliveryAssign,
) -> Delivery:
    delivery = await _get_delivery(db, tenant_id=tenant_id, delivery_id=delivery_id)
    if delivery.status not in {"PENDING", "ASSIGNED"}:
        raise AppError(
            "DELIVERY_NOT_ASSIGNABLE",
            f"Delivery status {delivery.status} cannot be reassigned",
            status_code=400,
        )

    partner = await partners_service.get_partner_profile(
        db, tenant_id=tenant_id, partner_id=payload.partner_id
    )
    if partner.status != "ACTIVE":
        raise AppError("PARTNER_NOT_ACTIVE", "Partner is not active", status_code=400)

    delivery.partner_id = partner.id
    delivery.vehicle_id = payload.vehicle_id
    delivery.status = "ASSIGNED"
    await db.commit()
    return await _get_delivery(db, tenant_id=tenant_id, delivery_id=delivery_id)


async def complete_stop(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    delivery_id: uuid.UUID,
    stop_id: uuid.UUID,
    payload: StopComplete,
) -> Delivery:
    delivery = await _get_delivery(db, tenant_id=tenant_id, delivery_id=delivery_id)
    stop = next((s for s in delivery.stops if s.id == stop_id), None)
    if not stop:
        raise AppError("STOP_NOT_FOUND", "Delivery stop not found", status_code=404)
    if stop.status == "COMPLETED":
        return delivery

    stop.status = "COMPLETED"
    stop.proof = payload.proof
    stop.completed_at = datetime.now(timezone.utc)

    if delivery.status == "ASSIGNED" and stop.stop_type == "PICKUP":
        delivery.status = "IN_PROGRESS"

    if all(s.status == "COMPLETED" for s in delivery.stops):
        delivery.status = "COMPLETED"

    await db.commit()
    return await _get_delivery(db, tenant_id=tenant_id, delivery_id=delivery_id)


async def list_my_deliveries(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    active_only: bool = True,
) -> list[Delivery]:
    profile = await partners_service.get_partner_profile_for_user(
        db, tenant_id=tenant_id, user_id=user_id
    )
    stmt = (
        select(Delivery)
        .options(selectinload(Delivery.stops))
        .where(
            Delivery.tenant_id == tenant_id,
            Delivery.partner_id == profile.id,
        )
        .order_by(Delivery.created_at.desc())
    )
    if active_only:
        stmt = stmt.where(Delivery.status.in_(["ASSIGNED", "IN_PROGRESS"]))
    return list(await db.scalars(stmt))


async def get_order_tracking(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    order_id: uuid.UUID,
) -> dict:
    from app.fulfillment.models import Fulfillment
    from app.orders.models import Order

    order = await db.scalar(
        select(Order).where(Order.id == order_id, Order.tenant_id == tenant_id)
    )
    if not order:
        raise AppError("ORDER_NOT_FOUND", "Order not found", status_code=404)

    fulfillment = await db.scalar(
        select(Fulfillment).where(
            Fulfillment.order_id == order_id,
            Fulfillment.tenant_id == tenant_id,
        )
    )

    delivery = None
    if fulfillment:
        delivery = await db.scalar(
            select(Delivery)
            .options(selectinload(Delivery.stops))
            .where(
                Delivery.fulfillment_id == fulfillment.id,
                Delivery.tenant_id == tenant_id,
            )
        )

    rider = None
    stops: list[dict] = []
    if delivery:
        stops = [
            {
                "id": s.id,
                "sequence": s.sequence,
                "stop_type": s.stop_type,
                "lat": s.lat,
                "lng": s.lng,
                "status": s.status,
            }
            for s in sorted(delivery.stops, key=lambda x: x.sequence)
        ]
        if delivery.partner_id:
            partner = await partners_service.get_partner_profile(
                db, tenant_id=tenant_id, partner_id=delivery.partner_id
            )
            if partner.current_lat is not None and partner.current_lng is not None:
                rider = {
                    "partner_id": partner.id,
                    "lat": partner.current_lat,
                    "lng": partner.current_lng,
                    "updated_at": partner.updated_at,
                    "is_online": partner.is_online,
                }

    return {
        "order_id": order.id,
        "order_status": order.status,
        "delivery_id": delivery.id if delivery else None,
        "delivery_status": delivery.status if delivery else None,
        "eta": delivery.eta if delivery else None,
        "rider": rider,
        "stops": stops,
    }
