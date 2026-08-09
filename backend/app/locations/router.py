"""Business location HTTP routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import AuthContext, require_permission, resolve_tenant_id
from app.core.errors import AppError
from app.locations import discovery, service
from app.locations.schemas import (
    BusinessLocationCreate,
    BusinessLocationRead,
    BusinessLocationUpdate,
    NearbyStoreRead,
)

router = APIRouter(tags=["locations"])


def _require_tenant(tenant_id: uuid.UUID | None) -> uuid.UUID:
    if tenant_id is None:
        raise AppError("TENANT_REQUIRED", "X-Tenant-ID header is required", 400)
    return tenant_id


@router.get("/stores/nearby", response_model=list[NearbyStoreRead])
async def nearby_stores(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(default=5.0, gt=0, le=50),
    type: str | None = Query(default=None, description="GROCERY or RETAIL"),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("stores.discover")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[NearbyStoreRead]:
    """Hyperlocal store discovery — active inventory+delivery locations near a point."""
    _ = ctx
    tid = _require_tenant(tenant_id)
    return await discovery.discover_nearby_stores(
        db,
        tenant_id=tid,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        business_type=type,
        limit=limit,
    )


@router.post(
    "/businesses/{business_id}/locations",
    response_model=BusinessLocationRead,
)
async def create_location(
    business_id: uuid.UUID,
    payload: BusinessLocationCreate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("business.settings")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> BusinessLocationRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    location = await service.create_location(
        db, tenant_id=tid, business_id=business_id, payload=payload
    )
    return BusinessLocationRead.model_validate(location)


@router.get(
    "/businesses/{business_id}/locations",
    response_model=list[BusinessLocationRead],
)
async def list_locations(
    business_id: uuid.UUID,
    active_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("locations.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[BusinessLocationRead]:
    _ = ctx
    tid = _require_tenant(tenant_id)
    rows = await service.list_locations(
        db, tenant_id=tid, business_id=business_id, active_only=active_only
    )
    return [BusinessLocationRead.model_validate(r) for r in rows]


@router.get(
    "/businesses/{business_id}/locations/{location_id}",
    response_model=BusinessLocationRead,
)
async def get_location(
    business_id: uuid.UUID,
    location_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("locations.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> BusinessLocationRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    location = await service.get_location(
        db, tenant_id=tid, business_id=business_id, location_id=location_id
    )
    return BusinessLocationRead.model_validate(location)


@router.patch(
    "/businesses/{business_id}/locations/{location_id}",
    response_model=BusinessLocationRead,
)
async def update_location(
    business_id: uuid.UUID,
    location_id: uuid.UUID,
    payload: BusinessLocationUpdate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("business.settings")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> BusinessLocationRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    location = await service.update_location(
        db,
        tenant_id=tid,
        business_id=business_id,
        location_id=location_id,
        payload=payload,
    )
    return BusinessLocationRead.model_validate(location)
