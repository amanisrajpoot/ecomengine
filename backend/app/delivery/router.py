"""Delivery HTTP routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import AuthContext, require_permission, resolve_tenant_id
from app.core.errors import AppError
from app.delivery import service
from app.delivery.schemas import (
    AssignDeliveryBody,
    CompleteStopBody,
    DeliveryCreateBody,
    DeliveryRead,
    DeliveryStopRead,
    DeliveryTransitionBody,
    TrackingUpdateBody,
)

router = APIRouter(tags=["delivery"])


def _require_tenant(tenant_id: uuid.UUID | None) -> uuid.UUID:
    if tenant_id is None:
        raise AppError("TENANT_REQUIRED", "X-Tenant-ID header is required", 400)
    return tenant_id


def _to_read(delivery, stops) -> DeliveryRead:
    base = DeliveryRead.model_validate(delivery)
    return base.model_copy(
        update={"stops": [DeliveryStopRead.model_validate(s) for s in stops]}
    )


@router.post("/fulfillments/{fulfillment_id}/deliveries", response_model=DeliveryRead)
async def create_delivery(
    fulfillment_id: uuid.UUID,
    payload: DeliveryCreateBody | None = None,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("delivery.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> DeliveryRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    delivery, stops = await service.create_delivery_for_fulfillment(
        db,
        tenant_id=tid,
        fulfillment_id=fulfillment_id,
        payload=payload or DeliveryCreateBody(),
    )
    return _to_read(delivery, stops)


@router.get("/deliveries/{delivery_id}", response_model=DeliveryRead)
async def get_delivery(
    delivery_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("delivery.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> DeliveryRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    return _to_read(*(await service.get_delivery(db, tenant_id=tid, delivery_id=delivery_id)))


@router.get("/fulfillments/{fulfillment_id}/delivery", response_model=DeliveryRead)
async def get_fulfillment_delivery(
    fulfillment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("delivery.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> DeliveryRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    graph = await service.get_by_fulfillment(db, tenant_id=tid, fulfillment_id=fulfillment_id)
    if not graph:
        raise AppError("DELIVERY_NOT_FOUND", "Delivery not found for fulfillment", 404)
    return _to_read(*graph)


@router.post("/deliveries/{delivery_id}/assign", response_model=DeliveryRead)
async def assign_delivery(
    delivery_id: uuid.UUID,
    payload: AssignDeliveryBody | None = None,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("delivery.assign")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> DeliveryRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    delivery, stops = await service.assign_delivery(
        db,
        tenant_id=tid,
        delivery_id=delivery_id,
        payload=payload or AssignDeliveryBody(),
    )
    return _to_read(delivery, stops)


@router.post("/deliveries/{delivery_id}/transitions", response_model=DeliveryRead)
async def transition_delivery(
    delivery_id: uuid.UUID,
    payload: DeliveryTransitionBody,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("delivery.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> DeliveryRead:
    tid = _require_tenant(tenant_id)
    delivery, stops = await service.transition_delivery(
        db,
        tenant_id=tid,
        delivery_id=delivery_id,
        payload=payload,
        actor_user_id=ctx.user.id,
    )
    return _to_read(delivery, stops)


@router.post("/deliveries/{delivery_id}/tracking", response_model=DeliveryRead)
async def update_tracking(
    delivery_id: uuid.UUID,
    payload: TrackingUpdateBody,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("delivery.track")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> DeliveryRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    delivery, stops = await service.update_tracking(
        db, tenant_id=tid, delivery_id=delivery_id, payload=payload
    )
    return _to_read(delivery, stops)


@router.post(
    "/deliveries/{delivery_id}/stops/{stop_id}/complete",
    response_model=DeliveryRead,
)
async def complete_stop(
    delivery_id: uuid.UUID,
    stop_id: uuid.UUID,
    payload: CompleteStopBody | None = None,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("delivery.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> DeliveryRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    delivery, stops = await service.complete_stop(
        db,
        tenant_id=tid,
        delivery_id=delivery_id,
        stop_id=stop_id,
        payload=payload or CompleteStopBody(),
    )
    return _to_read(delivery, stops)
