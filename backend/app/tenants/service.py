"""Tenant and platform config services."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.tenants.models import PlatformConfig, Tenant
from app.tenants.schemas import TenantConfig, TenantCreate


async def create_tenant(db: AsyncSession, payload: TenantCreate) -> Tenant:
    existing = await db.scalar(select(Tenant).where(Tenant.slug == payload.slug))
    if existing:
        raise AppError("TENANT_SLUG_EXISTS", "Tenant slug already exists", status_code=409)
    tenant = Tenant(
        name=payload.name,
        slug=payload.slug,
        status="ACTIVE",
        config=payload.config.model_dump(),
    )
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant


async def get_tenant(db: AsyncSession, tenant_id: uuid.UUID) -> Tenant:
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise AppError("TENANT_NOT_FOUND", "Tenant not found", status_code=404)
    return tenant


async def update_tenant_config(
    db: AsyncSession, tenant_id: uuid.UUID, config: TenantConfig
) -> Tenant:
    tenant = await get_tenant(db, tenant_id)
    tenant.config = config.model_dump()
    await db.commit()
    await db.refresh(tenant)
    return tenant


async def list_tenants(db: AsyncSession) -> list[Tenant]:
    result = await db.scalars(select(Tenant).order_by(Tenant.created_at.desc()))
    return list(result)


async def upsert_platform_config(db: AsyncSession, key: str, value: dict) -> PlatformConfig:
    row = await db.scalar(select(PlatformConfig).where(PlatformConfig.key == key))
    if row is None:
        row = PlatformConfig(key=key, value=value)
        db.add(row)
    else:
        row.value = value
    await db.commit()
    await db.refresh(row)
    return row


async def get_platform_config(db: AsyncSession, key: str) -> PlatformConfig:
    row = await db.scalar(select(PlatformConfig).where(PlatformConfig.key == key))
    if not row:
        raise AppError("PLATFORM_CONFIG_NOT_FOUND", "Platform config key not found", 404)
    return row
