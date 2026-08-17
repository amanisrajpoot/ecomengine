"""Business HTTP routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.businesses import service
from app.businesses.schemas import BusinessCreate, BusinessRead, BusinessUpdate
from app.core.db import get_db
from app.core.deps import AuthContext, require_permission, resolve_tenant_id
from app.core.errors import AppError

router = APIRouter(prefix="/businesses", tags=["businesses"])


def _require_tenant(tenant_id: uuid.UUID | None) -> uuid.UUID:
    if tenant_id is None:
        raise AppError("TENANT_REQUIRED", "X-Tenant-ID header is required", 400)
    return tenant_id


@router.post("", response_model=BusinessRead)
async def create_business(
    payload: BusinessCreate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("business.create")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> BusinessRead:
    tid = _require_tenant(tenant_id or ctx.tenant_id)
    business = await service.create_business(
        db, tenant_id=tid, payload=payload, owner_user_id=ctx.user.id
    )
    return BusinessRead.model_validate(business)


@router.get("", response_model=list[BusinessRead])
async def list_businesses(
    status: str | None = Query(default=None),
    type: str | None = Query(default=None, alias="type"),
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("businesses.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> list[BusinessRead]:
    _ = ctx
    tid = _require_tenant(tenant_id)
    rows = await service.list_businesses(
        db, tenant_id=tid, status=status, business_type=type
    )
    return [BusinessRead.model_validate(b) for b in rows]


@router.get("/{business_id}", response_model=BusinessRead)
async def get_business(
    business_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("businesses.read")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> BusinessRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    business = await service.get_business(db, tenant_id=tid, business_id=business_id)
    return BusinessRead.model_validate(business)


@router.patch("/{business_id}", response_model=BusinessRead)
async def update_business(
    business_id: uuid.UUID,
    payload: BusinessUpdate,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("business.settings")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> BusinessRead:
    _ = ctx
    tid = _require_tenant(tenant_id)
    business = await service.update_business(
        db, tenant_id=tid, business_id=business_id, payload=payload
    )
    return BusinessRead.model_validate(business)
