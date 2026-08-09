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
    "catalog.manage": {
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
        Role.STAFF,
    },
    "cart.manage": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
        Role.CUSTOMER,
    },
    "pricing.quote": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
        Role.BUSINESS_OWNER,
        Role.BUSINESS_MANAGER,
        Role.CUSTOMER,
    },
    "tax.manage": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
    },
    "tax.calculate": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
        Role.BUSINESS_OWNER,
        Role.BUSINESS_MANAGER,
    },
    "orders.create": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
        Role.CUSTOMER,
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
    "orders.transition": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
        Role.BUSINESS_OWNER,
        Role.BUSINESS_MANAGER,
        Role.STAFF,
        Role.DELIVERY_PARTNER,
        Role.CUSTOMER,
    },
    "payments.manage": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
        Role.CUSTOMER,
        Role.BUSINESS_OWNER,
    },
    "payments.refund": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
    },
    "ledger.read": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
        Role.BUSINESS_OWNER,
        Role.BUSINESS_MANAGER,
    },
    "ledger.adjust": {
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
    "settlements.approve": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
    },
    "fulfillment.read": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
        Role.BUSINESS_OWNER,
        Role.BUSINESS_MANAGER,
        Role.STAFF,
        Role.CUSTOMER,
        Role.DELIVERY_PARTNER,
    },
    "fulfillment.manage": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
        Role.BUSINESS_OWNER,
        Role.BUSINESS_MANAGER,
        Role.STAFF,
        Role.DELIVERY_PARTNER,
    },
    "partners.read": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
        Role.BUSINESS_OWNER,
        Role.BUSINESS_MANAGER,
        Role.DELIVERY_PARTNER,
    },
    "partners.manage": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
    },
    "partners.location": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
        Role.DELIVERY_PARTNER,
    },
    "delivery.read": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
        Role.BUSINESS_OWNER,
        Role.BUSINESS_MANAGER,
        Role.STAFF,
        Role.CUSTOMER,
        Role.DELIVERY_PARTNER,
    },
    "delivery.manage": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
        Role.BUSINESS_OWNER,
        Role.BUSINESS_MANAGER,
        Role.DELIVERY_PARTNER,
    },
    "delivery.assign": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
        Role.BUSINESS_MANAGER,
    },
    "delivery.track": {
        Role.SUPER_ADMIN,
        Role.TENANT_ADMIN,
        Role.DELIVERY_PARTNER,
        Role.BUSINESS_MANAGER,
    },
}


def roles_for(action: str) -> set[Role]:
    return PERMISSIONS.get(action, set())
