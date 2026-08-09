"""Ledger access helpers for merchant-scoped reads."""

from __future__ import annotations

import uuid

from app.core.deps import AuthContext
from app.core.errors import AppError
from app.identity.rbac import Role
from app.ledger.models import LedgerEntry
from app.orders.models import Order

ADMIN_LEDGER_ROLES = frozenset({Role.SUPER_ADMIN, Role.TENANT_ADMIN})
MERCHANT_LEDGER_ROLES = frozenset({Role.BUSINESS_OWNER, Role.BUSINESS_MANAGER})


def user_roles(ctx: AuthContext) -> set[Role]:
    return {Role(b.role) for b in ctx.roles if b.role in Role._value2member_map_}


def is_merchant_ledger_viewer(ctx: AuthContext) -> bool:
    roles = user_roles(ctx)
    if roles & ADMIN_LEDGER_ROLES:
        return False
    return bool(roles & MERCHANT_LEDGER_ROLES)


def merchant_business_ids(ctx: AuthContext) -> list[uuid.UUID]:
    ids: list[uuid.UUID] = []
    for binding in ctx.roles:
        if binding.role in {r.value for r in MERCHANT_LEDGER_ROLES} and binding.business_id:
            ids.append(binding.business_id)
    return list(dict.fromkeys(ids))


def assert_order_ledger_readable(ctx: AuthContext, order: Order) -> None:
    if not is_merchant_ledger_viewer(ctx):
        return
    allowed = merchant_business_ids(ctx)
    if order.business_id not in allowed:
        raise AppError("ORDER_NOT_FOUND", "Order not found", 404)


def assert_ledger_entries_readable(ctx: AuthContext, entries: list[LedgerEntry]) -> None:
    if not is_merchant_ledger_viewer(ctx):
        return
    allowed = set(merchant_business_ids(ctx))
    for entry in entries:
        if entry.order_id is None:
            raise AppError("LEDGER_EVENT_NOT_FOUND", "Ledger event not found", 404)


def resolve_business_scope(
    ctx: AuthContext, *, business_id: uuid.UUID | None
) -> list[uuid.UUID] | None:
    """Return business_ids filter for merchant viewers, or None for admins."""
    if not is_merchant_ledger_viewer(ctx):
        return None
    allowed = merchant_business_ids(ctx)
    if not allowed:
        return []
    if business_id is None:
        return allowed
    if business_id not in allowed:
        return []
    return [business_id]
