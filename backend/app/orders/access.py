"""Order access helpers for customer-scoped reads."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.cart.service import get_or_create_customer_profile
from app.core.deps import AuthContext
from app.core.errors import AppError
from app.identity.rbac import Role
from app.orders.models import Order

STAFF_ORDER_ROLES = frozenset(
    {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
        Role.BUSINESS_OWNER,
        Role.BUSINESS_MANAGER,
        Role.STAFF,
        Role.DELIVERY_PARTNER,
    }
)


def user_roles(ctx: AuthContext) -> set[Role]:
    return {Role(b.role) for b in ctx.roles if b.role in Role._value2member_map_}


def is_customer_only(ctx: AuthContext) -> bool:
    roles = user_roles(ctx)
    if Role.SUPER_ADMIN in roles:
        return False
    return bool(roles) and roles.isdisjoint(STAFF_ORDER_ROLES)


async def resolve_customer_profile_id(
    db: AsyncSession, *, tenant_id: uuid.UUID, ctx: AuthContext
) -> uuid.UUID:
    profile = await get_or_create_customer_profile(
        db, tenant_id=tenant_id, user_id=ctx.user.id
    )
    return profile.id


async def assert_order_readable(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    ctx: AuthContext,
    order: Order,
) -> None:
    if not is_customer_only(ctx):
        return
    customer_id = await resolve_customer_profile_id(db, tenant_id=tenant_id, ctx=ctx)
    if order.customer_id != customer_id:
        raise AppError("ORDER_NOT_FOUND", "Order not found", 404)
