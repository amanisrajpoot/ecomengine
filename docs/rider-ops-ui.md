# Rider ops UI (Phase 31)

Notifications and settlements surfaces for the Rider PWA, with backend scoping for delivery partners.

## Rider PWA

| Route | Purpose |
|-------|---------|
| `/notifications` | Order SMS alerts for assigned deliveries |
| `/settlements` | Read-only RIDER payout periods (labeled **Earnings** in nav) |
| `/settlements/[id]` | Payout detail + report JSON |

## Backend scoping

### Notifications (`notifications.read`)

- **Customers** — `user_id` filter (unchanged)
- **Riders** (`DELIVERY_PARTNER` without customer/admin roles) — notifications for orders linked to deliveries assigned to their partner profile
- **Admins / merchants** — tenant-wide (unchanged)

### Settlements (`settlements.read`)

- **Merchants** — `MERCHANT` party scoped to owned businesses (unchanged)
- **Riders** — `RIDER` party scoped to their delivery partner profile id
- **Admins** — tenant-wide

Riders cannot create or transition settlements.

## RBAC

Added `DELIVERY_PARTNER` to `notifications.read` and `settlements.read`.

## Demo flow

1. Complete a food delivery as **Rider** (:3002)
2. **Alerts** — see order lifecycle SMS entries for that job's order
3. **Admin** (:3003) → Settlements → New → RIDER + partner id → Calculate
4. **Rider** → **Earnings** → view payout period (read-only)

## API version

`0.31.0`
