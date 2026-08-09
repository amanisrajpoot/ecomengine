"""Delivery orchestration: create, assign V1, track, complete stops."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.events import event_bus
from app.delivery.geo import haversine_km, in_service_area
from app.delivery.models import Delivery, DeliveryStop
from app.delivery.schemas import (
    AssignDeliveryBody,
    CompleteStopBody,
    CustomerDeliveryTrackingRead,
    DeliveryCreateBody,
    DeliveryTransitionBody,
    StopCreate,
    TrackingUpdateBody,
)
from app.fulfillment.models import Fulfillment
from app.fulfillment.schemas import FulfillmentTransitionRequest
from app.fulfillment.service import transition_fulfillment
from app.locations.models import BusinessLocation
from app.orders.models import Order
from app.orders.schemas import OrderTransitionRequest
from app.orders.service import transition_order
from app.partners.models import DeliveryPartnerProfile, Vehicle

DELIVERY_TRANSITIONS: dict[str, frozenset[str]] = {
    "CREATED": frozenset({"OFFERED", "ASSIGNED", "CANCELLED"}),
    "OFFERED": frozenset({"ASSIGNED", "CREATED", "CANCELLED"}),
    "ASSIGNED": frozenset({"EN_ROUTE_PICKUP", "CANCELLED"}),
    "EN_ROUTE_PICKUP": frozenset({"AT_PICKUP", "CANCELLED", "FAILED"}),
    "AT_PICKUP": frozenset({"EN_ROUTE_DROP", "FAILED"}),
    "EN_ROUTE_DROP": frozenset({"AT_DROP", "FAILED"}),
    "AT_DROP": frozenset({"COMPLETED", "FAILED"}),
    "COMPLETED": frozenset(),
    "CANCELLED": frozenset(),
    "FAILED": frozenset(),
}


async def _get_fulfillment(
    db: AsyncSession, *, tenant_id: uuid.UUID, fulfillment_id: uuid.UUID
) -> Fulfillment:
    fulfillment = await db.scalar(
        select(Fulfillment).where(
            Fulfillment.id == fulfillment_id, Fulfillment.tenant_id == tenant_id
        )
    )
    if not fulfillment:
        raise AppError("FULFILLMENT_NOT_FOUND", "Fulfillment not found", 404)
    return fulfillment


async def _load_delivery(
    db: AsyncSession, *, tenant_id: uuid.UUID, delivery_id: uuid.UUID
) -> tuple[Delivery, list[DeliveryStop]]:
    delivery = await db.scalar(
        select(Delivery).where(Delivery.id == delivery_id, Delivery.tenant_id == tenant_id)
    )
    if not delivery:
        raise AppError("DELIVERY_NOT_FOUND", "Delivery not found", 404)
    stops = list(
        await db.scalars(
            select(DeliveryStop)
            .where(DeliveryStop.delivery_id == delivery.id)
            .order_by(DeliveryStop.sequence.asc())
        )
    )
    return delivery, stops


async def get_delivery(
    db: AsyncSession, *, tenant_id: uuid.UUID, delivery_id: uuid.UUID
) -> tuple[Delivery, list[DeliveryStop]]:
    return await _load_delivery(db, tenant_id=tenant_id, delivery_id=delivery_id)


async def get_by_fulfillment(
    db: AsyncSession, *, tenant_id: uuid.UUID, fulfillment_id: uuid.UUID
) -> tuple[Delivery, list[DeliveryStop]] | None:
    delivery = await db.scalar(
        select(Delivery).where(
            Delivery.tenant_id == tenant_id, Delivery.fulfillment_id == fulfillment_id
        )
    )
    if not delivery:
        return None
    return await _load_delivery(db, tenant_id=tenant_id, delivery_id=delivery.id)


TERMINAL_DELIVERY_STATUSES = frozenset({"COMPLETED", "CANCELLED", "FAILED"})


async def list_deliveries(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    partner_id: uuid.UUID | None = None,
    status: str | None = None,
    active_only: bool = False,
) -> list[tuple[Delivery, list[DeliveryStop]]]:
    stmt = select(Delivery).where(Delivery.tenant_id == tenant_id)
    if partner_id:
        stmt = stmt.where(Delivery.partner_id == partner_id)
    if status:
        stmt = stmt.where(Delivery.status == status)
    if active_only:
        stmt = stmt.where(Delivery.status.notin_(TERMINAL_DELIVERY_STATUSES))
    stmt = stmt.order_by(Delivery.created_at.desc())
    deliveries = list(await db.scalars(stmt))
    results: list[tuple[Delivery, list[DeliveryStop]]] = []
    for delivery in deliveries:
        results.append(await _load_delivery(db, tenant_id=tenant_id, delivery_id=delivery.id))
    return results


async def _default_stops(
    db: AsyncSession, *, order: Order, fulfillment: Fulfillment
) -> list[StopCreate]:
    pickup_address: dict[str, Any] = {}
    pickup_lat = None
    pickup_lng = None
    order_meta = order.metadata_json if isinstance(order.metadata_json, dict) else {}
    pickup_meta = order_meta.get("pickup") if isinstance(order_meta.get("pickup"), dict) else {}
    drop_meta_order = order_meta.get("drop") if isinstance(order_meta.get("drop"), dict) else {}

    if pickup_meta:
        pickup_address = pickup_meta.get("address") or {}
        if not isinstance(pickup_address, dict):
            pickup_address = {"line1": "Pickup"}
        pickup_lat = pickup_meta.get("lat")
        pickup_lng = pickup_meta.get("lng")
    elif order.location_id:
        loc = await db.get(BusinessLocation, order.location_id)
        if loc:
            pickup_address = loc.address or {}
            pickup_lat = loc.lat
            pickup_lng = loc.lng

    drop_meta = (fulfillment.metadata_json or {}).get("dropoff") or drop_meta_order or {}
    drop_address = drop_meta.get("address") if isinstance(drop_meta, dict) else {}
    if not isinstance(drop_address, dict):
        drop_address = {"line1": "Customer address"}
    drop_lat = drop_meta.get("lat") if isinstance(drop_meta, dict) else None
    drop_lng = drop_meta.get("lng") if isinstance(drop_meta, dict) else None
    # Sensible demo defaults near pickup when drop geo missing.
    if drop_lat is None and pickup_lat is not None:
        drop_lat = float(pickup_lat) + 0.01
    if drop_lng is None and pickup_lng is not None:
        drop_lng = float(pickup_lng) + 0.01

    if fulfillment.type == "MULTI_STOP":
        return [
            StopCreate(
                sequence=0,
                stop_type="PICKUP",
                address=pickup_address or {"line1": "Pickup"},
                lat=float(pickup_lat) if pickup_lat is not None else None,
                lng=float(pickup_lng) if pickup_lng is not None else None,
                contact=pickup_meta.get("contact") if isinstance(pickup_meta, dict) else {},
            ),
            StopCreate(
                sequence=1,
                stop_type="DROP",
                address=drop_address or {"line1": "Drop"},
                lat=float(drop_lat) if drop_lat is not None else None,
                lng=float(drop_lng) if drop_lng is not None else None,
                contact=drop_meta.get("contact") if isinstance(drop_meta, dict) else {},
            ),
        ]

    return [
        StopCreate(
            sequence=0,
            stop_type="PICKUP",
            address=pickup_address or {"line1": "Store"},
            lat=float(pickup_lat) if pickup_lat is not None else None,
            lng=float(pickup_lng) if pickup_lng is not None else None,
        ),
        StopCreate(
            sequence=1,
            stop_type="DROP",
            address=drop_address or {"line1": "Customer"},
            lat=float(drop_lat) if drop_lat is not None else None,
            lng=float(drop_lng) if drop_lng is not None else None,
        ),
    ]


async def create_delivery_for_fulfillment(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    fulfillment_id: uuid.UUID,
    payload: DeliveryCreateBody,
) -> tuple[Delivery, list[DeliveryStop]]:
    fulfillment = await _get_fulfillment(db, tenant_id=tenant_id, fulfillment_id=fulfillment_id)
    if fulfillment.type == "SELF_PICKUP":
        raise AppError(
            "FULFILLMENT_NO_DELIVERY",
            "SELF_PICKUP fulfillments do not create deliveries",
            400,
        )

    existing = await db.scalar(
        select(Delivery).where(Delivery.fulfillment_id == fulfillment.id)
    )
    if existing:
        return await _load_delivery(db, tenant_id=tenant_id, delivery_id=existing.id)

    order = await db.scalar(
        select(Order).where(Order.id == fulfillment.order_id, Order.tenant_id == tenant_id)
    )
    if not order:
        raise AppError("ORDER_NOT_FOUND", "Order not found", 404)

    # Courier packages are ready for pickup at payment confirm — hop PENDING→READY.
    if fulfillment.type == "MULTI_STOP" and fulfillment.status == "PENDING":
        for hop in ("ACCEPTED", "READY"):
            fulfillment = await _get_fulfillment(
                db, tenant_id=tenant_id, fulfillment_id=fulfillment.id
            )
            if fulfillment.status == hop:
                continue
            await transition_fulfillment(
                db,
                tenant_id=tenant_id,
                fulfillment_id=fulfillment.id,
                payload=FulfillmentTransitionRequest(
                    to_status=hop, actor="system", reason="courier_ready_for_pickup"
                ),
                actor_user_id=None,
            )
        fulfillment = await _get_fulfillment(
            db, tenant_id=tenant_id, fulfillment_id=fulfillment.id
        )

    stops_payload = list(payload.stops)
    if payload.auto_stops and not stops_payload:
        stops_payload = await _default_stops(db, order=order, fulfillment=fulfillment)
    if len(stops_payload) < 1:
        raise AppError("DELIVERY_STOPS_REQUIRED", "At least one stop is required", 400)

    delivery = Delivery(
        tenant_id=tenant_id,
        fulfillment_id=fulfillment.id,
        status="CREATED",
        eta=payload.eta,
        metadata_json={
            **(payload.metadata or {}),
            "order_id": str(order.id),
            "fulfillment_type": fulfillment.type,
        },
    )
    db.add(delivery)
    await db.flush()
    for stop in stops_payload:
        db.add(
            DeliveryStop(
                delivery_id=delivery.id,
                sequence=stop.sequence,
                stop_type=stop.stop_type,
                address=stop.address or {},
                lat=stop.lat,
                lng=stop.lng,
                contact=stop.contact or {},
                status="PENDING",
            )
        )
    await db.commit()
    await db.refresh(delivery)

    # Advance fulfillment toward logistics when still READY.
    if fulfillment.status == "READY":
        await transition_fulfillment(
            db,
            tenant_id=tenant_id,
            fulfillment_id=fulfillment.id,
            payload=FulfillmentTransitionRequest(
                to_status="AWAITING_PICKUP",
                actor="system",
                reason="delivery_created",
            ),
            actor_user_id=None,
        )

    await event_bus.publish(
        "DeliveryCreated",
        {
            "tenant_id": str(tenant_id),
            "delivery_id": str(delivery.id),
            "fulfillment_id": str(fulfillment.id),
        },
    )
    return await _load_delivery(db, tenant_id=tenant_id, delivery_id=delivery.id)


async def _pickup_coords(stops: list[DeliveryStop]) -> tuple[float, float] | None:
    for stop in stops:
        if stop.stop_type == "PICKUP" and stop.lat is not None and stop.lng is not None:
            return float(stop.lat), float(stop.lng)
    for stop in stops:
        if stop.lat is not None and stop.lng is not None:
            return float(stop.lat), float(stop.lng)
    return None


async def assign_delivery(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    delivery_id: uuid.UUID,
    payload: AssignDeliveryBody,
) -> tuple[Delivery, list[DeliveryStop]]:
    delivery, stops = await _load_delivery(db, tenant_id=tenant_id, delivery_id=delivery_id)
    if delivery.status not in {"CREATED", "OFFERED"}:
        raise AppError(
            "DELIVERY_NOT_ASSIGNABLE",
            f"Cannot assign delivery in status {delivery.status}",
            409,
        )

    partner: DeliveryPartnerProfile | None = None
    distance_km: float | None = None

    if payload.partner_id:
        partner = await db.scalar(
            select(DeliveryPartnerProfile).where(
                DeliveryPartnerProfile.id == payload.partner_id,
                DeliveryPartnerProfile.tenant_id == tenant_id,
            )
        )
        if not partner or partner.status != "ACTIVE":
            raise AppError("PARTNER_NOT_AVAILABLE", "Partner not available", 400)
    else:
        pickup = await _pickup_coords(stops)
        if not pickup:
            raise AppError(
                "PICKUP_LOCATION_REQUIRED",
                "Auto-assignment requires pickup lat/lng on stops",
                400,
            )
        pickup_lat, pickup_lng = pickup
        candidates = list(
            await db.scalars(
                select(DeliveryPartnerProfile).where(
                    DeliveryPartnerProfile.tenant_id == tenant_id,
                    DeliveryPartnerProfile.status == "ACTIVE",
                    DeliveryPartnerProfile.is_online.is_(True),
                    DeliveryPartnerProfile.current_lat.is_not(None),
                    DeliveryPartnerProfile.current_lng.is_not(None),
                )
            )
        )
        ranked: list[tuple[float, DeliveryPartnerProfile]] = []
        for cand in candidates:
            assert cand.current_lat is not None and cand.current_lng is not None
            if not in_service_area(
                partner_lat=float(cand.current_lat),
                partner_lng=float(cand.current_lng),
                pickup_lat=pickup_lat,
                pickup_lng=pickup_lng,
                service_area=cand.service_area,
            ):
                continue
            dist = haversine_km(
                float(cand.current_lat), float(cand.current_lng), pickup_lat, pickup_lng
            )
            ranked.append((dist, cand))
        ranked.sort(key=lambda x: x[0])
        if not ranked:
            raise AppError("NO_PARTNERS_AVAILABLE", "No online partners available", 409)
        distance_km, partner = ranked[0]

    vehicle_id = payload.vehicle_id
    if vehicle_id:
        vehicle = await db.scalar(
            select(Vehicle).where(
                Vehicle.id == vehicle_id,
                Vehicle.tenant_id == tenant_id,
                Vehicle.partner_id == partner.id,
            )
        )
        if not vehicle:
            raise AppError("VEHICLE_NOT_FOUND", "Vehicle not found for partner", 404)
    else:
        vehicle = await db.scalar(
            select(Vehicle).where(
                Vehicle.tenant_id == tenant_id,
                Vehicle.partner_id == partner.id,
                Vehicle.is_active.is_(True),
            )
        )
        vehicle_id = vehicle.id if vehicle else None

    delivery.partner_id = partner.id
    delivery.vehicle_id = vehicle_id
    delivery.status = "ASSIGNED" if payload.auto_accept else "OFFERED"
    meta = dict(delivery.metadata_json or {})
    meta["assignment"] = {
        "partner_id": str(partner.id),
        "distance_km": distance_km,
        "mode": "manual" if payload.partner_id else "nearest_v1",
        "assigned_at": datetime.now(UTC).isoformat(),
    }
    delivery.metadata_json = meta
    await db.commit()
    await db.refresh(delivery)

    # Courier: assignment moves order PAYMENT_CONFIRMED → PICKUP_ASSIGNED.
    fulfillment = await _get_fulfillment(
        db, tenant_id=tenant_id, fulfillment_id=delivery.fulfillment_id
    )
    order = await db.scalar(
        select(Order).where(Order.id == fulfillment.order_id, Order.tenant_id == tenant_id)
    )
    if (
        order
        and order.state_machine_profile == "COURIER"
        and order.status == "PAYMENT_CONFIRMED"
        and delivery.status == "ASSIGNED"
    ):
        try:
            await transition_order(
                db,
                tenant_id=tenant_id,
                order_id=order.id,
                payload=OrderTransitionRequest(
                    to_status="PICKUP_ASSIGNED",
                    actor="system",
                    reason="delivery_assigned",
                ),
                actor_user_id=None,
            )
        except AppError:
            pass

    await event_bus.publish(
        "DeliveryAssigned",
        {
            "tenant_id": str(tenant_id),
            "delivery_id": str(delivery.id),
            "partner_id": str(partner.id),
            "status": delivery.status,
        },
    )
    if order:
        await event_bus.publish(
            "RiderAssigned",
            {
                "tenant_id": str(tenant_id),
                "order_id": str(order.id),
                "delivery_id": str(delivery.id),
                "partner_id": str(partner.id),
            },
        )
    return await _load_delivery(db, tenant_id=tenant_id, delivery_id=delivery.id)


async def transition_delivery(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    delivery_id: uuid.UUID,
    payload: DeliveryTransitionBody,
    actor_user_id: uuid.UUID | None,
) -> tuple[Delivery, list[DeliveryStop]]:
    delivery, stops = await _load_delivery(db, tenant_id=tenant_id, delivery_id=delivery_id)
    allowed = DELIVERY_TRANSITIONS.get(delivery.status, frozenset())
    if payload.to_status not in allowed:
        raise AppError(
            "DELIVERY_ILLEGAL_TRANSITION",
            f"Cannot move delivery from {delivery.status} to {payload.to_status}",
            409,
        )
    previous = delivery.status
    delivery.status = payload.to_status
    meta = dict(delivery.metadata_json or {})
    meta["last_transition"] = {
        "from": previous,
        "to": payload.to_status,
        "reason": payload.reason,
    }
    delivery.metadata_json = meta
    await db.commit()
    await db.refresh(delivery)

    # Sync fulfillment / order on key milestones.
    fulfillment = await _get_fulfillment(
        db, tenant_id=tenant_id, fulfillment_id=delivery.fulfillment_id
    )
    if payload.to_status == "EN_ROUTE_PICKUP" and fulfillment.status == "AWAITING_PICKUP":
        await transition_fulfillment(
            db,
            tenant_id=tenant_id,
            fulfillment_id=fulfillment.id,
            payload=FulfillmentTransitionRequest(
                to_status="IN_TRANSIT", actor="rider", reason="delivery_en_route"
            ),
            actor_user_id=actor_user_id,
        )
    if payload.to_status == "COMPLETED":
        if fulfillment.status != "COMPLETED":
            # Hop to COMPLETED via allowed path when needed.
            if fulfillment.status == "AWAITING_PICKUP":
                await transition_fulfillment(
                    db,
                    tenant_id=tenant_id,
                    fulfillment_id=fulfillment.id,
                    payload=FulfillmentTransitionRequest(
                        to_status="IN_TRANSIT", actor="system", reason="delivery_complete"
                    ),
                    actor_user_id=actor_user_id,
                )
            fulfillment = await _get_fulfillment(
                db, tenant_id=tenant_id, fulfillment_id=delivery.fulfillment_id
            )
            if fulfillment.status == "IN_TRANSIT":
                await transition_fulfillment(
                    db,
                    tenant_id=tenant_id,
                    fulfillment_id=fulfillment.id,
                    payload=FulfillmentTransitionRequest(
                        to_status="COMPLETED", actor="rider", reason="delivery_complete"
                    ),
                    actor_user_id=actor_user_id,
                )
        order = await db.scalar(
            select(Order).where(Order.id == fulfillment.order_id, Order.tenant_id == tenant_id)
        )
        if order and order.status in {
            "READY",
            "PICKED_UP",
            "OUT_FOR_DELIVERY",
            "PICKUP_ASSIGNED",
            "IN_TRANSIT",
        }:
            # Best-effort: walk profile-specific path to DELIVERED.
            try:
                if order.status == "READY":
                    await transition_order(
                        db,
                        tenant_id=tenant_id,
                        order_id=order.id,
                        payload=OrderTransitionRequest(
                            to_status="PICKED_UP", actor="rider", reason="delivery_complete"
                        ),
                        actor_user_id=actor_user_id,
                    )
                    order = (
                        await db.scalar(select(Order).where(Order.id == order.id))
                    ) or order
                if order.status == "PICKUP_ASSIGNED":
                    await transition_order(
                        db,
                        tenant_id=tenant_id,
                        order_id=order.id,
                        payload=OrderTransitionRequest(
                            to_status="PICKED_UP", actor="rider", reason="delivery_complete"
                        ),
                        actor_user_id=actor_user_id,
                    )
                    order = (
                        await db.scalar(select(Order).where(Order.id == order.id))
                    ) or order
                if order.status == "PICKED_UP":
                    next_status = (
                        "IN_TRANSIT"
                        if order.state_machine_profile == "COURIER"
                        else "OUT_FOR_DELIVERY"
                    )
                    await transition_order(
                        db,
                        tenant_id=tenant_id,
                        order_id=order.id,
                        payload=OrderTransitionRequest(
                            to_status=next_status,
                            actor="rider",
                            reason="delivery_complete",
                        ),
                        actor_user_id=actor_user_id,
                    )
                    order = (
                        await db.scalar(select(Order).where(Order.id == order.id))
                    ) or order
                if order.status in {"OUT_FOR_DELIVERY", "IN_TRANSIT"}:
                    await transition_order(
                        db,
                        tenant_id=tenant_id,
                        order_id=order.id,
                        payload=OrderTransitionRequest(
                            to_status="DELIVERED", actor="rider", reason="delivery_complete"
                        ),
                        actor_user_id=actor_user_id,
                    )
            except AppError:
                pass

    await event_bus.publish(
        "DeliveryStatusChanged",
        {
            "tenant_id": str(tenant_id),
            "delivery_id": str(delivery.id),
            "from_status": previous,
            "to_status": payload.to_status,
        },
    )
    return await _load_delivery(db, tenant_id=tenant_id, delivery_id=delivery.id)


async def update_tracking(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    delivery_id: uuid.UUID,
    payload: TrackingUpdateBody,
) -> tuple[Delivery, list[DeliveryStop]]:
    delivery, stops = await _load_delivery(db, tenant_id=tenant_id, delivery_id=delivery_id)
    if not delivery.partner_id:
        raise AppError("DELIVERY_UNASSIGNED", "Delivery has no partner for tracking", 409)

    partner = await db.scalar(
        select(DeliveryPartnerProfile).where(
            DeliveryPartnerProfile.id == delivery.partner_id,
            DeliveryPartnerProfile.tenant_id == tenant_id,
        )
    )
    if partner:
        partner.current_lat = payload.lat
        partner.current_lng = payload.lng

    meta = dict(delivery.metadata_json or {})
    history = list(meta.get("tracking") or [])
    point = {
        "lat": payload.lat,
        "lng": payload.lng,
        "heading": payload.heading,
        "speed_kmh": payload.speed_kmh,
        "at": datetime.now(UTC).isoformat(),
    }
    history.append(point)
    meta["tracking"] = history[-50:]  # cap
    meta["last_location"] = point
    delivery.metadata_json = meta
    await db.commit()
    await db.refresh(delivery)
    await event_bus.publish(
        "DeliveryLocationUpdated",
        {"tenant_id": str(tenant_id), "delivery_id": str(delivery.id), **point},
    )
    return delivery, stops


async def complete_stop(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    delivery_id: uuid.UUID,
    stop_id: uuid.UUID,
    payload: CompleteStopBody,
) -> tuple[Delivery, list[DeliveryStop]]:
    delivery, stops = await _load_delivery(db, tenant_id=tenant_id, delivery_id=delivery_id)
    stop = next((s for s in stops if s.id == stop_id), None)
    if not stop:
        raise AppError("STOP_NOT_FOUND", "Delivery stop not found", 404)
    stop.status = "COMPLETED"
    stop.proof = payload.proof or {}
    stop.completed_at = datetime.now(UTC)
    await db.commit()

    async def _move(to_status: str, reason: str) -> None:
        await transition_delivery(
            db,
            tenant_id=tenant_id,
            delivery_id=delivery.id,
            payload=DeliveryTransitionBody(to_status=to_status, reason=reason),
            actor_user_id=None,
        )

    # Refresh status after commit; auto-advance along the logistics path.
    delivery, _ = await _load_delivery(db, tenant_id=tenant_id, delivery_id=delivery.id)
    if stop.stop_type == "PICKUP":
        if delivery.status == "ASSIGNED":
            await _move("EN_ROUTE_PICKUP", "pickup_stop_completed")
            delivery, _ = await _load_delivery(db, tenant_id=tenant_id, delivery_id=delivery.id)
        if delivery.status == "EN_ROUTE_PICKUP":
            await _move("AT_PICKUP", "pickup_stop_completed")
            delivery, _ = await _load_delivery(db, tenant_id=tenant_id, delivery_id=delivery.id)
        if delivery.status == "AT_PICKUP":
            await _move("EN_ROUTE_DROP", "pickup_stop_completed")
    elif stop.stop_type == "DROP":
        if delivery.status == "EN_ROUTE_DROP":
            await _move("AT_DROP", "drop_stop_completed")
            delivery, _ = await _load_delivery(db, tenant_id=tenant_id, delivery_id=delivery.id)
        if delivery.status == "AT_DROP":
            await _move("COMPLETED", "drop_stop_completed")

    return await _load_delivery(db, tenant_id=tenant_id, delivery_id=delivery.id)


async def get_order_delivery_tracking(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    order_id: uuid.UUID,
) -> CustomerDeliveryTrackingRead:
    from app.delivery.schemas import (
        DeliveryStopRead,
        LastLocationRead,
        RiderSummary,
    )
    from app.fulfillment.service import get_by_order

    graph = await get_by_order(db, tenant_id=tenant_id, order_id=order_id)
    if not graph:
        raise AppError("DELIVERY_NOT_FOUND", "Delivery not found for order", 404)
    fulfillment, _events = graph
    delivery_graph = await get_by_fulfillment(
        db, tenant_id=tenant_id, fulfillment_id=fulfillment.id
    )
    if not delivery_graph:
        raise AppError("DELIVERY_NOT_FOUND", "Delivery not found for order", 404)
    delivery, stops = delivery_graph

    partner_summary: RiderSummary | None = None
    if delivery.partner_id:
        partner = await db.get(DeliveryPartnerProfile, delivery.partner_id)
        if partner:
            partner_summary = RiderSummary(display_name=partner.display_name)

    last_location: LastLocationRead | None = None
    meta = delivery.metadata_json or {}
    raw_loc = meta.get("last_location")
    if isinstance(raw_loc, dict) and raw_loc.get("lat") is not None and raw_loc.get("lng") is not None:
        at_raw = raw_loc.get("at")
        at_dt: datetime | None = None
        if isinstance(at_raw, str):
            try:
                at_dt = datetime.fromisoformat(at_raw.replace("Z", "+00:00"))
            except ValueError:
                at_dt = None
        last_location = LastLocationRead(
            lat=float(raw_loc["lat"]),
            lng=float(raw_loc["lng"]),
            heading=raw_loc.get("heading"),
            speed_kmh=raw_loc.get("speed_kmh"),
            at=at_dt,
        )

    return CustomerDeliveryTrackingRead(
        delivery_id=delivery.id,
        status=delivery.status,
        eta=delivery.eta,
        stops=[DeliveryStopRead.model_validate(s) for s in stops],
        partner=partner_summary,
        last_location=last_location,
        fulfillment_status=fulfillment.status,
    )
