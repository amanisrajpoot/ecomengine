"""RBAC roles and permission checks."""

from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    SUPER_ADMIN = "SUPER_ADMIN"
    TENANT_ADMIN = "TENANT_ADMIN"
    BUSINESS_OWNER = "BUSINESS_OWNER"
    BUSINESS_MANAGER = "BUSINESS_MANAGER"
    STAFF = "STAFF"
    DELIVERY_PARTNER = "DELIVERY_PARTNER"
    CUSTOMER = "CUSTOMER"


# Action -> roles that may perform it (Phase 1 subset).
PERMISSIONS: dict[str, set[Role]] = {
    "tenants.manage": {Role.SUPER_ADMIN},
    "tenants.config": {Role.SUPER_ADMIN, Role.TENANT_ADMIN},
    "platform.config": {Role.SUPER_ADMIN},
    "users.roles.assign": {Role.SUPER_ADMIN, Role.TENANT_ADMIN},
    "business.create": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
        Role.BUSINESS_OWNER,
    },
    "business.settings": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
        Role.BUSINESS_OWNER,
        Role.BUSINESS_MANAGER,
    },
}


def roles_for(action: str) -> set[Role]:
    return PERMISSIONS.get(action, set())
