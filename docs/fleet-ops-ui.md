# Admin fleet ops UI (Phase 37)

Delivery partner and vehicle management for tenant ops, plus manual rider assignment on dispatch.

## Admin web screens

| Route | Purpose |
|-------|---------|
| `/fleet` | Partner list — online filter, live refresh |
| `/fleet/new` | Create partner profile for an existing user ID |
| `/fleet/[partnerId]` | Edit partner status/name, add vehicles |
| `/dispatch` | Enhanced — rider names on active deliveries |

## Dispatch improvements

`DispatchPanel` now supports:

- **Assign selected** — pick an online rider from dropdown
- **Auto-assign nearest** — existing V1 geo assignment

Requires `listDeliveryPartners` on the API client passed to the panel (admin dispatch uses full client).

## API usage

New `@commerce/api-client` methods:

- `getDeliveryPartner`, `createDeliveryPartner`, `updateDeliveryPartner`
- `listVehicles`, `createVehicle`

## Shared UI

- `PartnerCard` — display name, online indicator, status, last known location

## RBAC

- `partners.read` — list/get partners and vehicles
- `partners.manage` — create/update partners and vehicles
- `delivery.assign` — manual assignment (existing)

## Demo flow

1. Rider PWA (:3002) — login `rider@demo.com` → go **online**
2. Admin (:3003) → **Fleet** — see demo rider online
3. **Dispatch** — assign a waiting order to selected rider or auto-assign
4. Rider app — job appears under Deliveries

## API version

`0.37.0`
