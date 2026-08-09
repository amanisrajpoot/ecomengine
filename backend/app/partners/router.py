"""Partner / vehicle HTTP routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import AuthContext, require_permission, resolve_tenant_id
from app.core.errors import AppError
from app.partners import service
from app.partners.schemas import (
    PartnerCreate,
    PartnerLocationUpdate,
    PartnerRead,
    PartnerUpdate,
    VehicleCreate,
    VehicleRead,
)

router = APIRouter(tags=["partners"])


def _require_tenant(tenant_id: uuid.UUID | None) -> uuid.UUID:
    if tenant_id is None:
        raise AppError("TENANT_REQUIRED", "X-Tenant-ID header is required", 400)
    return tenant_id


@router.post("/delivery-partners", response_model=PartnerRead)
async def create_partner(
    payload: PartnerCreate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("partners.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> PartnerRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    partner = await service.create_partner(db, tenant_id=tid, payload=payload)
    return PartnerRead.model_validate(partner)


@router.get("/delivery-partners", response_model=list[PartnerRead])
async def list_partners(
    online_only: bool = Query(default=False),
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("partners.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[PartnerRead]:
    _ = ctx
    tid = _require_tenant(tenant_id)
    rows = await service.list_partners(
        db, tenant_id=tid, online_only=online_only, status=status
    )
    return [PartnerRead.model_validate(r) for r in rows]


@router.get("/delivery-partners/{partner_id}", response_model=PartnerRead)
async def get_partner(
    partner_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("partners.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> PartnerRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    partner = await service.get_partner(db, tenant_id=tid, partner_id=partner_id)
    return PartnerRead.model_validate(partner)


@router.patch("/delivery-partners/{partner_id}", response_model=PartnerRead)
async def update_partner(
    partner_id: uuid.UUID,
    payload: PartnerUpdate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("partners.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> PartnerRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    partner = await service.update_partner(
        db, tenant_id=tid, partner_id=partner_id, payload=payload
    )
    return PartnerRead.model_validate(partner)


@router.post("/delivery-partners/{partner_id}/location", response_model=PartnerRead)
async def update_partner_location(
    partner_id: uuid.UUID,
    payload: PartnerLocationUpdate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("partners.location")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> PartnerRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    partner = await service.update_partner_location(
        db, tenant_id=tid, partner_id=partner_id, payload=payload
    )
    return PartnerRead.model_validate(partner)


@router.post("/vehicles", response_model=VehicleRead)
async def create_vehicle(
    payload: VehicleCreate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("partners.manage")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> VehicleRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    vehicle = await service.create_vehicle(db, tenant_id=tid, payload=payload)
    return VehicleRead.model_validate(vehicle)


@router.get("/vehicles", response_model=list[VehicleRead])
async def list_vehicles(
    partner_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("partners.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[VehicleRead]:
    _ = ctx
    tid = _require_tenant(tenant_id)
    rows = await service.list_vehicles(db, tenant_id=tid, partner_id=partner_id)
    return [VehicleRead.model_validate(r) for r in rows]
