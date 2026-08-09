"""Tenant resolution and signature checks for ONDC ingress."""

from __future__ import annotations

import uuid

from fastapi import Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AppError
from app.tenants.models import Tenant


async def resolve_tenant_id(
    db: AsyncSession,
    *,
    tenant_header: str | None,
    bpp_id: str | None,
) -> uuid.UUID:
    if tenant_header:
        try:
            tid = uuid.UUID(tenant_header)
        except ValueError as exc:
            raise AppError("ONDc_TENANT_INVALID", "Invalid X-Tenant-ID", 400) from exc
        tenant = await db.get(Tenant, tid)
        if not tenant:
            raise AppError("TENANT_NOT_FOUND", "Tenant not found", 404)
        return tid

    if bpp_id:
        rows = await db.scalars(select(Tenant))
        for tenant in rows:
            cfg = tenant.config or {}
            ondc = cfg.get("ondc") if isinstance(cfg.get("ondc"), dict) else {}
            if ondc.get("bpp_id") == bpp_id:
                return tenant.id

    settings = get_settings()
    if settings.ondc_mock:
        raise AppError(
            "ONDc_TENANT_REQUIRED",
            "X-Tenant-ID header required in ONDC mock mode",
            400,
        )
    raise AppError("ONDc_TENANT_UNRESOLVED", "Could not resolve tenant for bpp_id", 401)


def assert_ingress_allowed(*, authorization: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if settings.ondc_mock:
        return
    if not authorization:
        raise AppError("ONDc_UNAUTHORIZED", "Authorization required for ONDC ingress", 401)
