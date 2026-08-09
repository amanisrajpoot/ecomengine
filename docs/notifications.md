# Notifications

Event-driven fan-out for order lifecycle updates. Core order/payment modules publish domain events; the notifications module subscribes and dispatches without those modules importing notification code.

## Channels

| Channel key | Adapter | Notes |
|-------------|---------|-------|
| `sms_mock` | `MockSmsChannel` | Default in dev; marks messages `SENT` and stores provider ref |

Configure via `NOTIFICATIONS_DEFAULT_CHANNEL` (default `sms_mock`).

## Events → SMS

Subscribed events:

- `OrderCreated`
- `PaymentCaptured`
- `OrderAccepted`
- `OrderReady`
- `OrderDelivered`
- `OrderCancelled`
- `RiderAssigned` (when published)

Recipient phone is resolved from order `metadata.customer_phone`, payment checkout payload, or customer user phone.

## API

- `GET /api/v1/notifications?order_id=` — list deliveries (`notifications.read`)
- Customers see only their own rows; tenant admins see all in tenant

## Persistence

`notifications` table stores every outbound message with status, provider ref, and body for ops/debugging.
