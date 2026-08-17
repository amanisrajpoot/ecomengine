"""Delivery partner HTTP routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import AuthContext, require_permission, resolve_tenant_id
from app.core.errors import AppError
from app.partners import service
from app.partners.schemas import (
    PartnerLocationUpdate,
    PartnerProfileCreate,
    PartnerProfileRead,
    PartnerProfileUpdate,
    VehicleCreate,
    VehicleRead,
)

router = APIRouter(prefix="/partners", tags=["partners"])


def _require_tenant(tenant_id: uuid.UUID | None) -> uuid.UUID:
    if tenant_id is None:
        raise AppError("TENANT_REQUIRED", "X-Tenant-ID header is required", 400)
    return tenant_id


@router.post("/profiles", response_model=PartnerProfileRead)
async def create_partner_profile(
    payload: PartnerProfileCreate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("partners.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> PartnerProfileRead:
    tid = _require_tenant(tenant_id)
    profile = await service.create_partner_profile(
        db, tenant_id=tid, user_id=ctx.user.id, payload=payload
    )
    return PartnerProfileRead.model_validate(profile)


@router.get("/profiles/me", response_model=PartnerProfileRead)
async def get_my_partner_profile(
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("partners.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> PartnerProfileRead:
    tid = _require_tenant(tenant_id)
    profile = await service.get_partner_profile_for_user(
        db, tenant_id=tid, user_id=ctx.user.id
    )
    return PartnerProfileRead.model_validate(profile)


@router.patch("/profiles/me", response_model=PartnerProfileRead)
async def update_my_partner_profile(
    payload: PartnerProfileUpdate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("partners.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> PartnerProfileRead:
    tid = _require_tenant(tenant_id)
    profile = await service.update_partner_profile(
        db, tenant_id=tid, user_id=ctx.user.id, payload=payload
    )
    return PartnerProfileRead.model_validate(profile)


@router.post("/profiles/me/location", response_model=PartnerProfileRead)
async def update_my_partner_location(
    payload: PartnerLocationUpdate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("partners.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> PartnerProfileRead:
    tid = _require_tenant(tenant_id)
    profile = await service.update_partner_location(
        db,
        tenant_id=tid,
        user_id=ctx.user.id,
        lat=payload.lat,
        lng=payload.lng,
    )
    return PartnerProfileRead.model_validate(profile)


@router.get("/profiles", response_model=list[PartnerProfileRead])
async def list_partner_profiles(
    online_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("partners.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[PartnerProfileRead]:
    _ = ctx
    tid = _require_tenant(tenant_id)
    rows = await service.list_available_partners(db, tenant_id=tid, online_only=online_only)
    return [PartnerProfileRead.model_validate(r) for r in rows]


@router.post("/vehicles", response_model=VehicleRead)
async def create_vehicle(
    payload: VehicleCreate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("partners.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> VehicleRead:
    tid = _require_tenant(tenant_id)
    vehicle = await service.create_vehicle(
        db, tenant_id=tid, user_id=ctx.user.id, payload=payload
    )
    return VehicleRead.model_validate(vehicle)


@router.get("/vehicles", response_model=list[VehicleRead])
async def list_my_vehicles(
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("partners.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[VehicleRead]:
    tid = _require_tenant(tenant_id)
    rows = await service.list_partner_vehicles(db, tenant_id=tid, user_id=ctx.user.id)
    return [VehicleRead.model_validate(r) for r in rows]
