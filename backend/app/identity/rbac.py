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


PERMISSIONS: dict[str, set[Role]] = {
    "tenants.manage": {Role.SUPER_ADMIN},
    "tenants.config": {Role.SUPER_ADMIN, Role.TENANT_ADMIN},
    "users.roles.assign": {Role.SUPER_ADMIN, Role.TENANT_ADMIN},
    "platform.config": {Role.SUPER_ADMIN},
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
    "locations.read": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
        Role.BUSINESS_OWNER,
        Role.BUSINESS_MANAGER,
        Role.STAFF,
    },
    "businesses.read": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
        Role.BUSINESS_OWNER,
        Role.BUSINESS_MANAGER,
        Role.STAFF,
        Role.CUSTOMER,
    },
    "catalog.read": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
        Role.BUSINESS_OWNER,
        Role.BUSINESS_MANAGER,
        Role.STAFF,
        Role.CUSTOMER,
    },
    "catalog.manage": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
        Role.BUSINESS_OWNER,
        Role.BUSINESS_MANAGER,
    },
    "inventory.read": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
        Role.BUSINESS_OWNER,
        Role.BUSINESS_MANAGER,
        Role.STAFF,
    },
    "inventory.manage": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
        Role.BUSINESS_OWNER,
        Role.BUSINESS_MANAGER,
    },
    "cart.read": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
        Role.CUSTOMER,
    },
    "cart.manage": {
        Role.SUPER_ADMIN,
        Role.CUSTOMER,
    },
    "taxes.read": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
        Role.BUSINESS_OWNER,
        Role.BUSINESS_MANAGER,
    },
    "taxes.manage": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
    },
    "orders.read": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
        Role.BUSINESS_OWNER,
        Role.BUSINESS_MANAGER,
        Role.STAFF,
        Role.CUSTOMER,
        Role.DELIVERY_PARTNER,
    },
    "orders.place": {
        Role.SUPER_ADMIN,
        Role.CUSTOMER,
    },
    "orders.manage": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
        Role.BUSINESS_OWNER,
        Role.BUSINESS_MANAGER,
        Role.STAFF,
        Role.DELIVERY_PARTNER,
    },
    "payments.create": {
        Role.SUPER_ADMIN,
        Role.CUSTOMER,
    },
    "payments.read": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
        Role.BUSINESS_OWNER,
        Role.BUSINESS_MANAGER,
        Role.STAFF,
        Role.CUSTOMER,
    },
    "payments.manage": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
        Role.BUSINESS_OWNER,
        Role.BUSINESS_MANAGER,
    },
    "ledger.read": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
        Role.BUSINESS_OWNER,
        Role.BUSINESS_MANAGER,
        Role.STAFF,
    },
    "ledger.manage": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
    },
    "settlements.read": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
        Role.BUSINESS_OWNER,
        Role.BUSINESS_MANAGER,
    },
    "settlements.manage": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
    },
}


def roles_for(action: str) -> set[Role]:
    return PERMISSIONS.get(action, set())
