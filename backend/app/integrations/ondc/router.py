"""ONDC BPP HTTP ingress — Beckn actions mapped to commerce engine."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db
from app.integrations.ondc.auth import assert_ingress_allowed, resolve_tenant_id
from app.integrations.ondc.schemas import BecknRequest, BecknResponse, OndcMetaRead
from app.integrations.ondc import service

router = APIRouter(prefix="/integrations/ondc", tags=["ondc"])


@router.get("/meta", response_model=OndcMetaRead)
async def ondc_meta() -> OndcMetaRead:
    settings = get_settings()
    return OndcMetaRead(
        mock_mode=settings.ondc_mock,
        supported_domains=["ONDC:RET10", "ONDC:RET11"],
        supported_actions=["search", "select", "init", "confirm", "status", "cancel"],
        version=settings.app_version,
    )


@router.post("/search", response_model=BecknResponse)
async def ondc_search(
    request: BecknRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(assert_ingress_allowed),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
) -> BecknResponse:
    tenant_id = await resolve_tenant_id(
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
    tenant_id = await resolve_tenant_id(
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
    tenant_id = await resolve_tenant_id(
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
    tenant_id = await resolve_tenant_id(
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
    tenant_id = await resolve_tenant_id(
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
    tenant_id = await resolve_tenant_id(
        db, tenant_header=x_tenant_id, bpp_id=request.context.bpp_id
    )
    return await service.handle_cancel(db, tenant_id=tenant_id, request=request)
