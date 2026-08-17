"""ONDC BPP adapter HTTP routes (Beckn-style actions)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import AuthContext, require_permission, resolve_tenant_id
from app.core.errors import AppError
from app.integrations.ondc import service
from app.integrations.ondc.schemas import (
    OndcConfirmRequest,
    OndcConfirmResponse,
    OndcContext,
    OndcInitRequest,
    OndcInitResponse,
    OndcSearchRequest,
    OndcSearchResponse,
    OndcSelectRequest,
    OndcSelectResponse,
    OndcStatusRequest,
    OndcStatusResponse,
)

router = APIRouter(prefix="/ondc", tags=["ondc"])


def _require_tenant(tenant_id: uuid.UUID | None) -> uuid.UUID:
    if tenant_id is None:
        raise AppError("TENANT_REQUIRED", "X-Tenant-ID header is required", 400)
    return tenant_id


def _response_context(context: OndcContext, action: str) -> OndcContext:
    return context.model_copy(
        update={
            "action": action,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@router.post("/search", response_model=OndcSearchResponse)
async def ondc_search(
    payload: OndcSearchRequest,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("integrations.ondc")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> OndcSearchResponse:
    _ = ctx
    tid = _require_tenant(tenant_id)
    message = await service.search_catalog(db, tenant_id=tid, message=payload.message)
    return OndcSearchResponse(
        context=_response_context(payload.context, "on_search"),
        message=message,
    )


@router.post("/select", response_model=OndcSelectResponse)
async def ondc_select(
    payload: OndcSelectRequest,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("integrations.ondc")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> OndcSelectResponse:
    _ = ctx
    tid = _require_tenant(tenant_id)
    message = await service.select_items(db, tenant_id=tid, message=payload.message)
    return OndcSelectResponse(
        context=_response_context(payload.context, "on_select"),
        message=message,
    )


@router.post("/init", response_model=OndcInitResponse)
async def ondc_init(
    payload: OndcInitRequest,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("integrations.ondc")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> OndcInitResponse:
    _ = ctx
    tid = _require_tenant(tenant_id)
    message = await service.init_order(db, tenant_id=tid, message=payload.message)
    return OndcInitResponse(
        context=_response_context(payload.context, "on_init"),
        message=message,
    )


@router.post("/confirm", response_model=OndcConfirmResponse)
async def ondc_confirm(
    payload: OndcConfirmRequest,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("integrations.ondc")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> OndcConfirmResponse:
    _ = ctx
    tid = _require_tenant(tenant_id)
    message = await service.confirm_order(db, tenant_id=tid, message=payload.message)
    return OndcConfirmResponse(
        context=_response_context(payload.context, "on_confirm"),
        message=message,
    )


@router.post("/status", response_model=OndcStatusResponse)
async def ondc_status(
    payload: OndcStatusRequest,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("integrations.ondc")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> OndcStatusResponse:
    _ = ctx
    tid = _require_tenant(tenant_id)
    message = await service.order_status(db, tenant_id=tid, message=payload.message)
    return OndcStatusResponse(
        context=_response_context(payload.context, "on_status"),
        message=message,
    )
