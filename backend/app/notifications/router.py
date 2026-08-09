"""Notification query HTTP routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import AuthContext, require_permission
from app.core.errors import AppError
from app.identity.rbac import Role
from app.notifications import service
from app.notifications.schemas import NotificationRead

router = APIRouter(prefix="/notifications", tags=["notifications"])

_ADMIN_ROLES = {
    Role.SUPER_ADMIN,
    Role.TENANT_ADMIN,
    Role.BUSINESS_OWNER,
    Role.BUSINESS_MANAGER,
}


@router.get("", response_model=list[NotificationRead])
async def list_notifications(
    order_id: uuid.UUID | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("notifications.read")),
) -> list[NotificationRead]:
    if ctx.tenant_id is None:
        raise AppError("TENANT_REQUIRED", "X-Tenant-ID is required", 400)
    user_roles = {Role(b.role) for b in ctx.roles if b.role in Role._value2member_map_}
    user_filter: uuid.UUID | None = None
    if user_roles.isdisjoint(_ADMIN_ROLES):
        user_filter = ctx.user.id
    rows = await service.list_notifications(
        db,
        tenant_id=ctx.tenant_id,
        order_id=order_id,
        user_id=user_filter,
        limit=limit,
    )
    return [NotificationRead.model_validate(row) for row in rows]
