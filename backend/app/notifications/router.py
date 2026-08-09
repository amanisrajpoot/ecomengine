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
from app.notifications.access import (
    ADMIN_NOTIFICATION_ROLES,
    is_rider_notification_viewer,
    resolve_rider_order_ids,
)
from app.notifications.schemas import NotificationRead
from app.orders.access import is_customer_only

router = APIRouter(prefix="/notifications", tags=["notifications"])


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
    order_ids: list[uuid.UUID] | None = None

    if user_roles.isdisjoint(ADMIN_NOTIFICATION_ROLES):
        if is_customer_only(ctx):
            user_filter = ctx.user.id
        elif is_rider_notification_viewer(ctx):
            order_ids = await resolve_rider_order_ids(
                db, tenant_id=ctx.tenant_id, ctx=ctx
            )
            if order_id and order_id not in order_ids:
                return []
            if order_id:
                order_ids = [order_id]
        else:
            user_filter = ctx.user.id

    rows = await service.list_notifications(
        db,
        tenant_id=ctx.tenant_id,
        order_id=order_id,
        user_id=user_filter,
        order_ids=order_ids,
        limit=limit,
    )
    return [NotificationRead.model_validate(row) for row in rows]
