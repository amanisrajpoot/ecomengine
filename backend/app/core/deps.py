"""FastAPI dependencies for auth, tenancy, and RBAC."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.errors import AppError
from app.core.security import decode_access_token
from app.identity.models import User, UserRoleBinding
from app.identity.rbac import Role, roles_for
from app.tenants.models import Tenant

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class AuthContext:
    user: User
    roles: list[UserRoleBinding]
    tenant_id: uuid.UUID | None


async def resolve_tenant_id(
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
    db: AsyncSession = Depends(get_db),
) -> uuid.UUID | None:
    if not x_tenant_id:
        return None
    try:
        tenant_uuid = uuid.UUID(x_tenant_id)
    except ValueError as exc:
        raise AppError("INVALID_TENANT_ID", "X-Tenant-ID must be a UUID", 400) from exc
    tenant = await db.get(Tenant, tenant_uuid)
    if not tenant:
        raise AppError("TENANT_NOT_FOUND", "Tenant not found", 404)
    if tenant.status != "ACTIVE":
        raise AppError("TENANT_SUSPENDED", "Tenant is not active", 403)
    return tenant.id


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
    header_tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> AuthContext:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError("UNAUTHENTICATED", "Missing bearer token", 401)
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = uuid.UUID(payload["sub"])
    except Exception as exc:  # noqa: BLE001
        raise AppError("INVALID_TOKEN", "Invalid or expired token", 401) from exc

    user = await db.get(User, user_id)
    if not user or user.status != "ACTIVE":
        raise AppError("UNAUTHENTICATED", "User not found or disabled", 401)

    bindings = list(
        await db.scalars(select(UserRoleBinding).where(UserRoleBinding.user_id == user.id))
    )
    is_super = any(b.role == Role.SUPER_ADMIN.value for b in bindings)

    # Enforce tenant boundary: non-super users must match header tenant when provided.
    if header_tenant_id is not None and not is_super:
        if user.tenant_id is not None and user.tenant_id != header_tenant_id:
            raise AppError("FORBIDDEN_TENANT", "Cross-tenant access denied", 403)
        allowed = any(
            b.role == Role.SUPER_ADMIN.value
            or b.tenant_id is None
            or b.tenant_id == header_tenant_id
            for b in bindings
        )
        if not allowed and user.tenant_id != header_tenant_id:
            raise AppError("FORBIDDEN_TENANT", "Cross-tenant access denied", 403)

    return AuthContext(user=user, roles=bindings, tenant_id=header_tenant_id or user.tenant_id)


def require_roles(*allowed: Role):
    allowed_set = set(allowed)

    async def _dependency(ctx: AuthContext = Depends(get_current_user)) -> AuthContext:
        user_roles = {Role(b.role) for b in ctx.roles if b.role in Role._value2member_map_}
        if Role.SUPER_ADMIN in user_roles:
            return ctx
        if user_roles.isdisjoint(allowed_set):
            raise AppError("FORBIDDEN", "Insufficient role", 403)
        return ctx

    return _dependency


def require_permission(action: str):
    allowed = roles_for(action)

    async def _dependency(ctx: AuthContext = Depends(get_current_user)) -> AuthContext:
        user_roles = {Role(b.role) for b in ctx.roles if b.role in Role._value2member_map_}
        if Role.SUPER_ADMIN in user_roles:
            return ctx
        if user_roles.isdisjoint(allowed):
            raise AppError("FORBIDDEN", f"Missing permission for {action}", 403)
        return ctx

    return _dependency
