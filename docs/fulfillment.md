# Fulfillment & Delivery

## Separation

```text
Order
  │
  ▼
Fulfillment
  │
  ▼
Delivery (when logistics required)
```

Orders must not embed rider assignment or multi-stop routing fields as first-class order columns. Those belong to fulfillment/delivery.

---

## Fulfillment types

| Type | Use |
|------|-----|
| `DELIVERY` | Food / hyperlocal to customer |
| `PICKUP` | Courier pickup leg / partner pickup |
| `SELF_PICKUP` | Customer collects |
| `SCHEDULED` | Time-windowed fulfillment |
| `MULTI_STOP` | Courier pickup + drop (and future batching) |

Same order engine; fulfillment type selected at checkout from business capabilities.

---

## Vertical mapping

| Vertical | Typical fulfillment |
|----------|---------------------|
| Food | `DELIVERY` |
| Grocery / hyperlocal | `DELIVERY` |
| Retail | `SELF_PICKUP` or `DELIVERY` |
| Courier | `MULTI_STOP` (pickup + drop) |

---

## Delivery model

```text
Delivery
 ├── pickup stop(s)
 ├── destination stop(s)
 ├── partner
 ├── vehicle
 ├── status
 ├── ETA
 └── tracking
```

### DeliveryStop

- `sequence`
- `type` (`PICKUP` / `DROP`)
- `address`, `geo`
- `contact`
- `status`
- `proof` (OTP / photo / signature metadata)

### DeliveryPartner

- KYC/documents
- availability / online flag
- `current_location`
- service area

### Vehicle

- type, registration, capacity hints

---

## Assignment algorithm V1

Keep it simple:

```text
Find available riders
  ↓
Filter by service area
  ↓
Calculate distance to pickup
  ↓
Rank nearest riders
  ↓
Offer job
  ↓
Timeout
  ↓
Next rider
```

Later (explicitly not V1): batching, route optimization, demand prediction, dynamic pricing.

---

## Tracking

- Rider location updates via WebSockets (phase when rider PWA lands)
- Customer order tracking reads delivery + order status projections

---

## Proof of delivery

Courier and optionally food/hyperlocal:

- OTP
- Photo
- Signature metadata

Stored on stop / delivery completion event; triggers `OrderDelivered` when policy says order completes.

---

## Phase 11 APIs (fulfillment only)

- `GET /api/v1/orders/{id}/fulfillment`
- `POST /api/v1/orders/{id}/fulfillment` — idempotent create after payment confirm
- `GET /api/v1/fulfillments` / `GET /api/v1/fulfillments/{id}`
- `POST /api/v1/fulfillments/{id}/transitions`

Created automatically when an order reaches `PAYMENT_CONFIRMED`. Order transitions sync the fulfillment projection (`PENDING` → … → `COMPLETED`) without storing rider/vehicle on `Order`.

---

## Phase 12 APIs (delivery)

### Partners / vehicles
- `POST/GET /api/v1/delivery-partners`, `PATCH`, `POST .../location`
- `POST/GET /api/v1/vehicles`

### Deliveries
- `POST /api/v1/fulfillments/{id}/deliveries` — create with pickup/drop stops (not for `SELF_PICKUP`)
- `GET /api/v1/deliveries/{id}` / `GET /api/v1/fulfillments/{id}/delivery`
- `POST /api/v1/deliveries/{id}/assign` — V1 nearest online partner (or explicit `partner_id`)
- `POST /api/v1/deliveries/{id}/transitions`
- `POST /api/v1/deliveries/{id}/tracking` — REST location ping (WebSockets later)
- `POST /api/v1/deliveries/{id}/stops/{stop_id}/complete` — OTP/photo/signature proof

Assignment V1: online `ACTIVE` partners with location → filter service area radius → rank by haversine to pickup → assign nearest.
