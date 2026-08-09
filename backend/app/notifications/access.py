"""Notification access helpers for rider-scoped reads."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import AuthContext
from app.delivery.models import Delivery
from app.fulfillment.models import Fulfillment
from app.identity.rbac import Role
from app.partners.service import get_partner_for_user

ADMIN_NOTIFICATION_ROLES = frozenset(
    {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
        Role.BUSINESS_OWNER,
        Role.BUSINESS_MANAGER,
    }
)
RIDER_NOTIFICATION_ROLES = frozenset({Role.DELIVERY_PARTNER})


def user_roles(ctx: AuthContext) -> set[Role]:
    return {Role(b.role) for b in ctx.roles if b.role in Role._value2member_map_}


def is_rider_notification_viewer(ctx: AuthContext) -> bool:
    roles = user_roles(ctx)
    if roles & ADMIN_NOTIFICATION_ROLES:
        return False
    return bool(roles & RIDER_NOTIFICATION_ROLES)


async def assigned_order_ids_for_partner(
    db: AsyncSession, *, tenant_id: uuid.UUID, partner_id: uuid.UUID
) -> list[uuid.UUID]:
    stmt = (
        select(Fulfillment.order_id)
        .join(Delivery, Delivery.fulfillment_id == Fulfillment.id)
        .where(
            Fulfillment.tenant_id == tenant_id,
            Delivery.tenant_id == tenant_id,
            Delivery.partner_id == partner_id,
        )
        .distinct()
    )
    return list(await db.scalars(stmt))


async def resolve_rider_order_ids(
    db: AsyncSession, *, tenant_id: uuid.UUID, ctx: AuthContext
) -> list[uuid.UUID]:
    partner = await get_partner_for_user(db, tenant_id=tenant_id, user_id=ctx.user.id)
    if not partner:
        return []
    return await assigned_order_ids_for_partner(
        db, tenant_id=tenant_id, partner_id=partner.id
    )
