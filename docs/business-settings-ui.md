# Business settings UI (Phase 36)

Merchant self-service for business profile and locations — uses Phase 2 business/location APIs.

## Merchant PWA screens

| Route | Purpose |
|-------|---------|
| `/settings` | Settings hub |
| `/settings/business` | Edit name, description, contact, prep time, ACTIVE/PAUSED |
| `/settings/locations` | List locations (active + inactive) |
| `/settings/locations/new` | Create location with address, geo, weekly hours |
| `/settings/locations/[locationId]` | Edit location details and hours |

## API usage

New/extended `@commerce/api-client` methods:

- `getBusiness` → full `Business` type
- `updateBusiness`
- `getLocation`, `createLocation`, `updateLocation`

## Shared UI

- `LocationCard` — location name, address summary, active badge

## RBAC

- `business.settings` — update business, create/update locations
- `locations.read` — list/get locations
- `businesses.read` — get business detail

`BUSINESS_OWNER` and `BUSINESS_MANAGER` have `business.settings`.

Capabilities are **read-only** in the UI (set at business type / onboarding).

## Demo flow

1. Merchant (:3001) → **Settings** → **Business profile**
2. Update prep time or pause a store
3. **Locations** → open Indiranagar kitchen → edit hours
4. Customer browse — paused business hidden from active flows

## API version

`0.36.0`
