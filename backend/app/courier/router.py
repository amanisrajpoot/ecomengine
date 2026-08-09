"""Courier HTTP routes — quote + shipment checkout."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import AuthContext, require_permission, resolve_tenant_id
from app.core.errors import AppError
from app.courier import service
from app.courier.quote import quote_fare
from app.courier.schemas import CourierQuoteRead, CourierQuoteRequest, CourierShipmentCreate
from app.orders.schemas import OrderItemRead, OrderRead, OrderStatusEventRead
from app.taxation.schemas import TaxKind
from app.taxation.service import load_rules_for_calculation

router = APIRouter(prefix="/courier", tags=["courier"])


def _require_tenant(tenant_id: uuid.UUID | None) -> uuid.UUID:
    if tenant_id is None:
        raise AppError("TENANT_REQUIRED", "X-Tenant-ID header is required", 400)
    return tenant_id


def _to_order_read(order, items, events) -> OrderRead:
    data = OrderRead.model_validate(order)
    data.items = [OrderItemRead.model_validate(i) for i in items]
    data.status_events = [OrderStatusEventRead.model_validate(e) for e in events]
    return data


@router.post("/quote", response_model=CourierQuoteRead)
async def courier_quote(
    payload: CourierQuoteRequest,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("courier.quote")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> CourierQuoteRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    rules = await load_rules_for_calculation(
        db, tenant_id=tid, kind=TaxKind.CUSTOMER_TRANSACTION.value
    )
    return quote_fare(payload, tax_rules=rules)


@router.post("/shipments", response_model=OrderRead)
async def create_courier_shipment(
    payload: CourierShipmentCreate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("orders.create")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> OrderRead:
    tid = _require_tenant(tenant_id)
    order, items, events = await service.create_shipment(
        db, tenant_id=tid, user_id=ctx.user.id, payload=payload
    )
    return _to_order_read(order, items, events)
