"""Fulfillment HTTP routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import AuthContext, require_permission, resolve_tenant_id
from app.core.errors import AppError
from app.fulfillment import service
from app.fulfillment.schemas import FulfillmentRead, FulfillmentTransition

router = APIRouter(tags=["fulfillment"])


def _require_tenant(tenant_id: uuid.UUID | None) -> uuid.UUID:
    if tenant_id is None:
        raise AppError("TENANT_REQUIRED", "X-Tenant-ID header is required", 400)
    return tenant_id


@router.get("/fulfillments", response_model=list[FulfillmentRead])
async def list_fulfillments(
    status: str | None = Query(default=None),
    type: str | None = Query(default=None, alias="type"),
    business_id: uuid.UUID | None = Query(default=None),
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
        business_id=business_id,
    )
    return [FulfillmentRead.model_validate(r) for r in rows]


@router.get("/fulfillments/{fulfillment_id}", response_model=FulfillmentRead)
async def get_fulfillment(
    fulfillment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("fulfillment.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> FulfillmentRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    row = await service.get_fulfillment(db, tenant_id=tid, fulfillment_id=fulfillment_id)
    return FulfillmentRead.model_validate(row)


@router.get("/orders/{order_id}/fulfillment", response_model=FulfillmentRead)
async def get_order_fulfillment(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("fulfillment.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> FulfillmentRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    row = await service.get_fulfillment_for_order(db, tenant_id=tid, order_id=order_id)
    return FulfillmentRead.model_validate(row)


@router.post("/fulfillments/{fulfillment_id}/transition", response_model=FulfillmentRead)
async def transition_fulfillment(
    fulfillment_id: uuid.UUID,
    payload: FulfillmentTransition,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("fulfillment.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> FulfillmentRead:
    tid = _require_tenant(tenant_id)
    row = await service.transition_fulfillment(
        db,
        tenant_id=tid,
        fulfillment_id=fulfillment_id,
        payload=payload,
        actor_user_id=ctx.user.id,
    )
    return FulfillmentRead.model_validate(row)
