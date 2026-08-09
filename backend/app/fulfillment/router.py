"""Fulfillment HTTP routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import AuthContext, require_permission, resolve_tenant_id
from app.core.errors import AppError
from app.fulfillment import service
from app.fulfillment.schemas import (
    FulfillmentCreateBody,
    FulfillmentRead,
    FulfillmentStatusEventRead,
    FulfillmentTransitionRequest,
)
from app.orders.access import assert_order_readable
from app.orders.service import get_order

router = APIRouter(tags=["fulfillment"])


def _require_tenant(tenant_id: uuid.UUID | None) -> uuid.UUID:
    if tenant_id is None:
        raise AppError("TENANT_REQUIRED", "X-Tenant-ID header is required", 400)
    return tenant_id


def _to_read(fulfillment, events) -> FulfillmentRead:
    base = FulfillmentRead.model_validate(fulfillment)
    return base.model_copy(
        update={
            "status_events": [
                FulfillmentStatusEventRead.model_validate(e) for e in events
            ]
        }
    )


@router.get("/fulfillments", response_model=list[FulfillmentRead])
async def list_fulfillments(
    status: str | None = None,
    type: str | None = None,
    order_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("fulfillment.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[FulfillmentRead]:
    _ = ctx
    tid = _require_tenant(tenant_id)
    rows = await service.list_fulfillments(
        db,
        tenant_id=tid,
        status=status,
        fulfillment_type=type,
        order_id=order_id,
    )
    result: list[FulfillmentRead] = []
    for row in rows:
        graph = await service.get_fulfillment(db, tenant_id=tid, fulfillment_id=row.id)
        result.append(_to_read(*graph))
    return result


@router.get("/fulfillments/{fulfillment_id}", response_model=FulfillmentRead)
async def get_fulfillment(
    fulfillment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("fulfillment.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> FulfillmentRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    return _to_read(*(await service.get_fulfillment(db, tenant_id=tid, fulfillment_id=fulfillment_id)))


@router.get("/orders/{order_id}/fulfillment", response_model=FulfillmentRead)
async def get_order_fulfillment(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("fulfillment.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> FulfillmentRead:
    tid = _require_tenant(tenant_id)
    order, _items, _events = await get_order(db, tenant_id=tid, order_id=order_id)
    await assert_order_readable(db, tenant_id=tid, ctx=ctx, order=order)
    graph = await service.get_by_order(db, tenant_id=tid, order_id=order_id)
    if not graph:
        raise AppError("FULFILLMENT_NOT_FOUND", "Fulfillment not found for order", 404)
    return _to_read(*graph)


@router.post("/orders/{order_id}/fulfillment", response_model=FulfillmentRead)
async def create_order_fulfillment(
    order_id: uuid.UUID,
    payload: FulfillmentCreateBody | None = None,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("fulfillment.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> FulfillmentRead:
    tid = _require_tenant(tenant_id)
    graph = await service.create_for_order(
        db,
        tenant_id=tid,
        order_id=order_id,
        payload=payload or FulfillmentCreateBody(),
        actor_user_id=ctx.user.id,
    )
    return _to_read(*graph)


@router.post("/fulfillments/{fulfillment_id}/transitions", response_model=FulfillmentRead)
async def transition_fulfillment(
    fulfillment_id: uuid.UUID,
    payload: FulfillmentTransitionRequest,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("fulfillment.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> FulfillmentRead:
    tid = _require_tenant(tenant_id)
    graph = await service.transition_fulfillment(
        db,
        tenant_id=tid,
        fulfillment_id=fulfillment_id,
        payload=payload,
        actor_user_id=ctx.user.id,
    )
    return _to_read(*graph)
