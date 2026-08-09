# Customer order tracking polish (Phase 39)

Richer live tracking for customers using scoped delivery APIs and Phase 33 UI primitives.

## Customer PWA screens

| Route | Changes |
|-------|---------|
| `/orders` | Active vs past sections, live polling, store names, skeletons |
| `/orders/[orderId]` | `usePolling`, `LiveIndicator`, status timeline, business name |
| `/cart` | Cashfree `return_url` lands on order detail (`{order_id}` placeholder) |

## API

| Method | Path | Notes |
|--------|------|-------|
| `GET` | `/api/v1/orders/{order_id}/delivery` | Customer-scoped; sanitized tracking payload |
| `GET` | `/api/v1/orders/{order_id}/fulfillment` | Now enforces order ownership for customers |

**`CustomerDeliveryTrackingRead`** includes: delivery status, ETA, stops, rider display name, last known location, fulfillment status.

Checkout `return_url` supports `{order_id}` substitution server-side.

## API client

- `getOrderDelivery(orderId)`

## Shared UI

- `OrderTrackingPanel` v2 — stops, ETA, rider name, last location, `usePolling` + `LiveIndicator`
- `OrderStatusTimeline` — order `status_events` on detail page

## Security

Customers can only read delivery/fulfillment for their own orders (404 otherwise).

## Demo flow

1. Customer places order → opens order detail
2. Merchant marks **Ready** → admin/merchant assigns rider
3. Rider goes en route and pings location
4. Customer sees rider name, stop progress, and coordinates update live

## API version

`0.39.0`
