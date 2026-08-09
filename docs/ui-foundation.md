# UI foundation + live notifications (Phase 33)

Shared UI primitives and client-side live notification layer across all four experience apps.

## UI foundation (`@commerce/ui`)

| Component / hook | Purpose |
|------------------|---------|
| `ToastProvider` / `useToast` | In-app toast stack (success, error, warning) |
| `Modal` / `ConfirmModal` | Accessible overlay dialogs |
| `Skeleton`, `SkeletonText`, `SkeletonCard` | Loading placeholders |
| `Badge` | Nav count pill (cart-style) |
| `ErrorState` | Error panel with retry action |
| `LiveIndicator` | Pulsing dot + refresh interval label |
| `usePolling` | Generic interval fetch hook |
| `useNotificationFeed` | Poll notifications + `localStorage` last-seen unread |
| `NavNotificationBadge` | Nav unread count for alerts |
| `NotificationFeed` | Full notifications page with live refresh |

Unread counts use **client-side** `localStorage` keys (`ce.<app>.notifications.lastSeen`) compared to `notification.created_at`. No backend `read_at` column in v1.

## Live notifications

### Nav badges

All four apps show an unread badge on Alerts / Notifications when signed in (admin requires tenant context).

### Notification pages

`/notifications` in each app uses `NotificationFeed`:

- Polls every 10s while open
- Marks feed as seen on visit (clears nav badge)
- Skeleton loaders on first fetch
- Order deep-links where applicable (customer, merchant, admin debugger)

### Order detail

`OrderNotificationsPanel` polls every 5s while the order view is open.

### Merchant kitchen board

`/orders` detects new `PAYMENT_CONFIRMED` kitchen orders on poll and fires a success toast.

## Demo flow

1. `pnpm demo:seed` and start PWAs (:3000–3003)
2. **Customer** — place a COD order
3. **Merchant** (:3001) — kitchen board shows live dot; new order toast on poll
4. **Merchant** nav Alerts badge increments; open Alerts → badge clears, feed refreshes
5. **Customer** (:3000) — Alerts badge + live feed on order SMS events
6. **Admin** (:3003) — tenant notifications with optional order filter

## API version

`0.33.0`
