"""Tenant management services."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.tenants.models import PlatformConfig, Tenant
from app.tenants.schemas import TenantCreate, TenantUpdate


async def create_tenant(db: AsyncSession, *, payload: TenantCreate) -> Tenant:
    existing = await db.scalar(select(Tenant).where(Tenant.slug == payload.slug))
    if existing:
        raise AppError("TENANT_SLUG_IN_USE", "Tenant slug already exists", 409)

    tenant = Tenant(
        name=payload.name,
        slug=payload.slug,
        status="ACTIVE",
        config=payload.config,
    )
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant


async def get_tenant(db: AsyncSession, *, tenant_id: uuid.UUID) -> Tenant:
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise AppError("TENANT_NOT_FOUND", "Tenant not found", 404)
    return tenant


async def list_tenants(db: AsyncSession) -> list[Tenant]:
    return list(await db.scalars(select(Tenant).order_by(Tenant.created_at.desc())))


async def update_tenant(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    payload: TenantUpdate,
) -> Tenant:
    tenant = await get_tenant(db, tenant_id=tenant_id)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(tenant, key, value)
    await db.commit()
    await db.refresh(tenant)
    return tenant


async def get_platform_config(db: AsyncSession, *, key: str) -> PlatformConfig | None:
    return await db.scalar(select(PlatformConfig).where(PlatformConfig.key == key))


async def upsert_platform_config(
    db: AsyncSession,
    *,
    key: str,
    value: dict,
) -> PlatformConfig:
    row = await get_platform_config(db, key=key)
    if row:
        row.value = value
    else:
        row = PlatformConfig(key=key, value=value)
        db.add(row)
    await db.commit()
    await db.refresh(row)
    return row
