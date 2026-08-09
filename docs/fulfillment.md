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
