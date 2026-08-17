"""Courier quote HTTP routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import AuthContext, require_permission, resolve_tenant_id
from app.core.errors import AppError
from app.pricing import service
from app.pricing.schemas import CourierQuoteRequest, CourierQuoteResponse

router = APIRouter(tags=["pricing"])


def _require_tenant(tenant_id: uuid.UUID | None) -> uuid.UUID:
    if tenant_id is None:
        raise AppError("TENANT_REQUIRED", "X-Tenant-ID header is required", 400)
    return tenant_id


@router.post("/courier/quote", response_model=CourierQuoteResponse)
async def quote_courier(
    payload: CourierQuoteRequest,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("cart.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> CourierQuoteResponse:
    _ = ctx
    tid = _require_tenant(tenant_id)
    breakdown, quote = await service.quote_courier_delivery(
        db, tenant_id=tid, payload=payload
    )
    return CourierQuoteResponse(breakdown=breakdown, quote=quote)
