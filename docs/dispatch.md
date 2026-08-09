# Dispatch & logistics (Phase 24)

## Flow

```text
Merchant marks READY (or courier PAYMENT_CONFIRMED)
        ↓ automatic (event handler)
Create Delivery + assign nearest online rider
        ↓
Rider PWA shows job → POD → order DELIVERED
```

If auto-dispatch fails (e.g. no rider online), merchant or admin can **Request rider** / **Retry** from the dispatch panel.

## Auto-dispatch

| Trigger | Profiles |
|---------|----------|
| `OrderReady` | `FOOD_DELIVERY`, `HYPERLOCAL_DELIVERY` |
| `PaymentCaptured` | `COURIER` |

Requirements for nearest-rider assignment:

- Partner `ACTIVE`, `is_online`, with `current_lat` / `current_lng`
- Pickup coordinates on delivery stops (from store location or courier metadata)
- Within partner service area when configured

Failures publish `DispatchFailed` (e.g. `NO_PARTNERS_AVAILABLE`).

## UI

| App | Surface |
|-----|---------|
| **Merchant** | Order detail → Dispatch panel |
| **Admin** | `/dispatch` — awaiting rider queue + active deliveries |
| **Rider** | Jobs list (unchanged; shows after assignment) |

## Demo flow (no curl)

1. **Rider** (:3002) — login → **Go online** first
2. **Customer** — place food order
3. **Merchant** — Accept → Preparing → **Ready** (auto-dispatch runs)
4. **Rider** — job appears → complete POD
5. **Admin** — optional dispatch board if retry needed

Courier: book shipment in Customer app → rider online → auto-assign on payment confirm.

## API (used by apps)

- `POST /api/v1/fulfillments/{id}/deliveries`
- `POST /api/v1/deliveries/{id}/assign`
- `GET /api/v1/fulfillments/{id}/delivery`
