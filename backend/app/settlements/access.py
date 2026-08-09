"""Settlement access helpers for merchant-scoped reads."""

from __future__ import annotations

import uuid

from app.core.deps import AuthContext
from app.core.errors import AppError
from app.identity.rbac import Role
from app.settlements.models import Settlement

ADMIN_SETTLEMENT_ROLES = frozenset({Role.SUPER_ADMIN, Role.TENANT_ADMIN})
MERCHANT_SETTLEMENT_ROLES = frozenset({Role.BUSINESS_OWNER, Role.BUSINESS_MANAGER})


def user_roles(ctx: AuthContext) -> set[Role]:
    return {Role(b.role) for b in ctx.roles if b.role in Role._value2member_map_}


def is_merchant_settlement_viewer(ctx: AuthContext) -> bool:
    roles = user_roles(ctx)
    if roles & ADMIN_SETTLEMENT_ROLES:
        return False
    return bool(roles & MERCHANT_SETTLEMENT_ROLES)


def merchant_business_ids(ctx: AuthContext) -> list[uuid.UUID]:
    ids: list[uuid.UUID] = []
    for binding in ctx.roles:
        if binding.role in {r.value for r in MERCHANT_SETTLEMENT_ROLES} and binding.business_id:
            ids.append(binding.business_id)
    return list(dict.fromkeys(ids))


def assert_settlement_readable(ctx: AuthContext, settlement: Settlement) -> None:
    if not is_merchant_settlement_viewer(ctx):
        return
    allowed = merchant_business_ids(ctx)
    if settlement.party_type != "MERCHANT" or settlement.party_id not in allowed:
        raise AppError("SETTLEMENT_NOT_FOUND", "Settlement not found", 404)


def assert_settlement_read_readable(
    ctx: AuthContext, *, party_type: str, party_id: uuid.UUID
) -> None:
    if not is_merchant_settlement_viewer(ctx):
        return
    allowed = merchant_business_ids(ctx)
    if party_type != "MERCHANT" or party_id not in allowed:
        raise AppError("SETTLEMENT_NOT_FOUND", "Settlement not found", 404)
