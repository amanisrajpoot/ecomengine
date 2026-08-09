# Merchant staff UI (Phase 38)

Business-scoped staff listing and role assignment for merchant owners.

## Merchant PWA screens

| Route | Purpose |
|-------|---------|
| `/settings/staff` | List staff/owners/managers; add by email |

Linked from the **Settings** hub.

## API

New business-scoped endpoints:

| Method | Path | Permission |
|--------|------|------------|
| `GET` | `/api/v1/businesses/{business_id}/staff` | `business.staff.read` |
| `POST` | `/api/v1/businesses/{business_id}/staff` | `business.staff.manage` |

**Assign body** — one of `user_id`, `email`, or `phone`, plus `role`:

- `STAFF` — kitchen/counter access (catalog, orders, inventory)
- `BUSINESS_MANAGER` — settings + staff read (cannot assign staff)

Owners (`BUSINESS_OWNER`) appear in the list but are assigned at business creation or via tenant admin.

## API client

- `listBusinessStaff(businessId)`
- `assignBusinessStaff(businessId, { email?, user_id?, phone?, role? })`

## Shared UI

- `StaffCard` — display name/email, role badge

## RBAC

| Permission | Roles |
|------------|-------|
| `business.staff.read` | SUPER_ADMIN, TENANT_ADMIN, BUSINESS_OWNER, BUSINESS_MANAGER |
| `business.staff.manage` | SUPER_ADMIN, TENANT_ADMIN, BUSINESS_OWNER |

Tenant admins can still use `POST /api/v1/users/{user_id}/roles` for any role.

## Demo flow

1. Register a new user in the tenant (or use demo merchant account).
2. Merchant (:3001) → **Settings** → **Staff**
3. Add `staff@demo.com` (or another registered email) as **Staff**
4. Log in as that user — access orders/catalog for the selected business

## API version

`0.38.0`
