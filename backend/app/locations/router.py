"""Business location HTTP routes (nested under businesses)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import AuthContext, require_permission, resolve_tenant_id
from app.core.errors import AppError
from app.locations import service
from app.locations.schemas import LocationCreate, LocationRead, LocationUpdate

router = APIRouter(prefix="/businesses/{business_id}/locations", tags=["locations"])


def _require_tenant(tenant_id: uuid.UUID | None) -> uuid.UUID:
    if tenant_id is None:
        raise AppError("TENANT_REQUIRED", "X-Tenant-ID header is required", 400)
    return tenant_id


@router.post("", response_model=LocationRead)
async def create_location(
    business_id: uuid.UUID,
    payload: LocationCreate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("business.settings")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> LocationRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    location = await service.create_location(
        db, tenant_id=tid, business_id=business_id, payload=payload
    )
    return LocationRead.model_validate(location)


@router.get("", response_model=list[LocationRead])
async def list_locations(
    business_id: uuid.UUID,
    active_only: bool = Query(default=True),
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("locations.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[LocationRead]:
    _ = ctx
    tid = _require_tenant(tenant_id)
    rows = await service.list_locations(
        db, tenant_id=tid, business_id=business_id, active_only=active_only
    )
    return [LocationRead.model_validate(row) for row in rows]


@router.get("/{location_id}", response_model=LocationRead)
async def get_location(
    business_id: uuid.UUID,
    location_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("locations.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> LocationRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    location = await service.get_location(
        db, tenant_id=tid, business_id=business_id, location_id=location_id
    )
    return LocationRead.model_validate(location)


@router.patch("/{location_id}", response_model=LocationRead)
async def update_location(
    business_id: uuid.UUID,
    location_id: uuid.UUID,
    payload: LocationUpdate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("business.settings")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> LocationRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    location = await service.update_location(
        db,
        tenant_id=tid,
        business_id=business_id,
        location_id=location_id,
        payload=payload,
    )
    return LocationRead.model_validate(location)
