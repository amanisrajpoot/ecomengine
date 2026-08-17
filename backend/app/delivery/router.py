"""Delivery HTTP routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import AuthContext, require_permission, resolve_tenant_id
from app.core.errors import AppError
from app.delivery import service
from app.delivery.schemas import (
    DeliveryAssign,
    DeliveryCreate,
    DeliveryRead,
    DeliveryStopRead,
    OrderTrackingRead,
    StopComplete,
)

router = APIRouter(tags=["delivery"])


def _require_tenant(tenant_id: uuid.UUID | None) -> uuid.UUID:
    if tenant_id is None:
        raise AppError("TENANT_REQUIRED", "X-Tenant-ID header is required", 400)
    return tenant_id


def _to_read(delivery) -> DeliveryRead:
    return DeliveryRead(
        id=delivery.id,
        tenant_id=delivery.tenant_id,
        fulfillment_id=delivery.fulfillment_id,
        partner_id=delivery.partner_id,
        vehicle_id=delivery.vehicle_id,
        status=delivery.status,
        eta=delivery.eta,
        created_at=delivery.created_at,
        updated_at=delivery.updated_at,
        stops=[DeliveryStopRead.model_validate(s) for s in delivery.stops],
    )


@router.post("/fulfillments/{fulfillment_id}/deliveries", response_model=DeliveryRead)
async def create_delivery(
    fulfillment_id: uuid.UUID,
    payload: DeliveryCreate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("delivery.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> DeliveryRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    delivery = await service.create_delivery_for_fulfillment(
        db,
        tenant_id=tid,
        fulfillment_id=fulfillment_id,
        payload=payload,
    )
    return _to_read(delivery)


@router.get("/fulfillments/{fulfillment_id}/delivery", response_model=DeliveryRead)
async def get_fulfillment_delivery(
    fulfillment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("delivery.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> DeliveryRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    delivery = await service.get_delivery_for_fulfillment(
        db, tenant_id=tid, fulfillment_id=fulfillment_id
    )
    return _to_read(delivery)


@router.get("/deliveries/me", response_model=list[DeliveryRead])
async def list_my_deliveries(
    active_only: bool = Query(default=True),
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("delivery.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[DeliveryRead]:
    tid = _require_tenant(tenant_id)
    deliveries = await service.list_my_deliveries(
        db,
        tenant_id=tid,
        user_id=ctx.user.id,
        active_only=active_only,
    )
    return [_to_read(d) for d in deliveries]


@router.get("/deliveries/{delivery_id}", response_model=DeliveryRead)
async def get_delivery(
    delivery_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("delivery.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> DeliveryRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    delivery = await service.get_delivery(db, tenant_id=tid, delivery_id=delivery_id)
    return _to_read(delivery)


@router.post("/deliveries/{delivery_id}/assign", response_model=DeliveryRead)
async def assign_delivery(
    delivery_id: uuid.UUID,
    payload: DeliveryAssign,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("delivery.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> DeliveryRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    delivery = await service.assign_delivery(
        db, tenant_id=tid, delivery_id=delivery_id, payload=payload
    )
    return _to_read(delivery)


@router.post(
    "/deliveries/{delivery_id}/stops/{stop_id}/complete",
    response_model=DeliveryRead,
)
async def complete_stop(
    delivery_id: uuid.UUID,
    stop_id: uuid.UUID,
    payload: StopComplete,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("delivery.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> DeliveryRead:
    tid = _require_tenant(tenant_id)
    delivery = await service.complete_stop(
        db,
        tenant_id=tid,
        delivery_id=delivery_id,
        stop_id=stop_id,
        payload=payload,
    )
    return _to_read(delivery)


@router.get("/orders/{order_id}/tracking", response_model=OrderTrackingRead)
async def get_order_tracking(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("orders.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> OrderTrackingRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    snapshot = await service.get_order_tracking(db, tenant_id=tid, order_id=order_id)
    return OrderTrackingRead.model_validate(snapshot)
