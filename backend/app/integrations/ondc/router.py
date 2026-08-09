"""ONDC BPP HTTP ingress — Beckn actions mapped to commerce engine."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db
from app.core.deps import AuthContext, require_permission, resolve_tenant_id
from app.core.errors import AppError
from app.integrations.ondc.auth import assert_ingress_allowed, resolve_tenant_id as resolve_ondc_tenant
from app.integrations.ondc.schemas import BecknRequest, BecknResponse, OndcMetaRead, OndcSessionRead
from app.integrations.ondc import service

router = APIRouter(prefix="/integrations/ondc", tags=["ondc"])


def _require_tenant(tenant_id: uuid.UUID | None) -> uuid.UUID:
    if tenant_id is None:
        raise AppError("TENANT_REQUIRED", "X-Tenant-ID header is required", 400)
    return tenant_id


@router.get("/meta", response_model=OndcMetaRead)
async def ondc_meta() -> OndcMetaRead:
    settings = get_settings()
    return OndcMetaRead(
        mock_mode=settings.ondc_mock,
        supported_domains=["ONDC:RET10", "ONDC:RET11"],
        supported_actions=["search", "select", "init", "confirm", "status", "cancel"],
        version=settings.app_version,
    )


@router.get("/sessions", response_model=list[OndcSessionRead])
async def list_ondc_sessions(
    stage: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("ondc.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[OndcSessionRead]:
    _ = ctx
    tid = _require_tenant(tenant_id)
    rows = await service.list_sessions(db, tenant_id=tid, stage=stage, limit=limit)
    return [OndcSessionRead.model_validate(row) for row in rows]


@router.get("/sessions/{session_id}", response_model=OndcSessionRead)
async def get_ondc_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("ondc.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> OndcSessionRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    row = await service.get_session(db, tenant_id=tid, session_id=session_id)
    return OndcSessionRead.model_validate(row)


@router.post("/search", response_model=BecknResponse)
async def ondc_search(
    request: BecknRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(assert_ingress_allowed),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
) -> BecknResponse:
    tenant_id = await resolve_ondc_tenant(
        db, tenant_header=x_tenant_id, bpp_id=request.context.bpp_id
    )
    return await service.handle_search(db, tenant_id=tenant_id, request=request)


@router.post("/select", response_model=BecknResponse)
async def ondc_select(
    request: BecknRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(assert_ingress_allowed),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
) -> BecknResponse:
    tenant_id = await resolve_ondc_tenant(
        db, tenant_header=x_tenant_id, bpp_id=request.context.bpp_id
    )
    return await service.handle_select(db, tenant_id=tenant_id, request=request)


@router.post("/init", response_model=BecknResponse)
async def ondc_init(
    request: BecknRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(assert_ingress_allowed),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
) -> BecknResponse:
    tenant_id = await resolve_ondc_tenant(
        db, tenant_header=x_tenant_id, bpp_id=request.context.bpp_id
    )
    return await service.handle_init(db, tenant_id=tenant_id, request=request)


@router.post("/confirm", response_model=BecknResponse)
async def ondc_confirm(
    request: BecknRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(assert_ingress_allowed),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
) -> BecknResponse:
    tenant_id = await resolve_ondc_tenant(
        db, tenant_header=x_tenant_id, bpp_id=request.context.bpp_id
    )
    return await service.handle_confirm(db, tenant_id=tenant_id, request=request)


@router.post("/status", response_model=BecknResponse)
async def ondc_status(
    request: BecknRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(assert_ingress_allowed),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
) -> BecknResponse:
    tenant_id = await resolve_ondc_tenant(
        db, tenant_header=x_tenant_id, bpp_id=request.context.bpp_id
    )
    return await service.handle_status(db, tenant_id=tenant_id, request=request)


@router.post("/cancel", response_model=BecknResponse)
async def ondc_cancel(
    request: BecknRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(assert_ingress_allowed),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
) -> BecknResponse:
    tenant_id = await resolve_ondc_tenant(
        db, tenant_header=x_tenant_id, bpp_id=request.context.bpp_id
    )
    return await service.handle_cancel(db, tenant_id=tenant_id, request=request)
