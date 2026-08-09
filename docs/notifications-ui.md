# Notifications UI (Phase 29)

Expose Phase 21 SMS notification deliveries in the experience apps.

## Admin web

| Route | Purpose |
|-------|---------|
| `/notifications` | Tenant-wide delivery log with optional order ID filter |
| Order debugger | Per-order notification feed via `OrderNotificationsPanel` |

## Customer PWA

| Route | Purpose |
|-------|---------|
| `/notifications` | SMS updates scoped to the signed-in customer |
| Order detail | Per-order notification feed |

## Merchant PWA

| Route | Purpose |
|-------|---------|
| `/notifications` | Tenant-wide log (business owner / manager roles) |

## Backend scoping

`GET /api/v1/notifications` (`notifications.read`):

- **Customers** — auto-filtered to `user_id` of the caller
- **Admin roles** (SUPER_ADMIN, TENANT_ADMIN, BUSINESS_OWNER, BUSINESS_MANAGER) — tenant-wide

Optional query params: `order_id`, `limit` (default 50, max 200).

## Shared UI

- `NotificationCard` — status badge, event name, body, recipient, timestamp
- `OrderNotificationsPanel` — fetches notifications for a single order

## api-client

`listNotifications({ order_id?, limit? })`

## Demo flow

1. **Customer** (:3000) — place a COD order (phone from profile/checkout)
2. **Customer** → Alerts or order detail → see `OrderCreated` / `PaymentCaptured` SMS mock entries
3. **Merchant** (:3001) → Alerts → tenant-wide feed
4. **Admin** (:3003) → Notifications or order debugger feed

## API version

`0.29.0`
