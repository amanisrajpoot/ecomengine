"""Tenant HTTP routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import AuthContext, require_permission
from app.tenants import service
from app.tenants.schemas import PlatformConfigRead, PlatformConfigUpsert, TenantCreate, TenantRead, TenantUpdate

router = APIRouter(prefix="/tenants", tags=["tenants"])
platform_router = APIRouter(prefix="/platform", tags=["platform"])


@router.post("", response_model=TenantRead)
async def create_tenant(
    payload: TenantCreate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("tenants.manage")),
) -> TenantRead:
    _ = ctx
    tenant = await service.create_tenant(db, payload=payload)
    return TenantRead.model_validate(tenant)


@router.get("", response_model=list[TenantRead])
async def list_tenants(
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("tenants.manage")),
) -> list[TenantRead]:
    _ = ctx
    tenants = await service.list_tenants(db)
    return [TenantRead.model_validate(t) for t in tenants]


@router.get("/{tenant_id}", response_model=TenantRead)
async def get_tenant(
    tenant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("tenants.config")),
) -> TenantRead:
    _ = ctx
    tenant = await service.get_tenant(db, tenant_id=tenant_id)
    return TenantRead.model_validate(tenant)


@router.patch("/{tenant_id}", response_model=TenantRead)
async def update_tenant(
    tenant_id: uuid.UUID,
    payload: TenantUpdate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("tenants.config")),
) -> TenantRead:
    _ = ctx
    tenant = await service.update_tenant(db, tenant_id=tenant_id, payload=payload)
    return TenantRead.model_validate(tenant)


@platform_router.get("/config/{key}", response_model=PlatformConfigRead)
async def get_platform_config(
    key: str,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("platform.config")),
) -> PlatformConfigRead:
    _ = ctx
    row = await service.get_platform_config(db, key=key)
    if not row:
        from app.core.errors import AppError

        raise AppError("CONFIG_NOT_FOUND", "Platform config not found", 404)
    return PlatformConfigRead.model_validate(row)


@platform_router.put("/config/{key}", response_model=PlatformConfigRead)
async def upsert_platform_config(
    key: str,
    payload: PlatformConfigUpsert,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("platform.config")),
) -> PlatformConfigRead:
    _ = ctx
    row = await service.upsert_platform_config(db, key=key, value=payload.value)
    return PlatformConfigRead.model_validate(row)
