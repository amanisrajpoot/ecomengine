# Order State Machines

## Principle

Order status is driven by a **configurable state machine**, not by hardcoded vertical enums inside the `Order` class.

Each business (or business type profile) selects a **state machine profile**:

| Profile | Typical vertical |
|---------|------------------|
| `FOOD_DELIVERY` | Food |
| `HYPERLOCAL_DELIVERY` | Grocery / retail delivery |
| `COURIER` | Intra-city courier |
| `PICKUP_ONLY` | Retail pickup (later) |

Storage:

- `orders.status` — current state string
- `orders.state_machine_profile` — profile key
- Transition validation via registry in `orders` module

---

## Shared early states

Most paid flows share:

```text
CREATED → PAYMENT_PENDING → PAYMENT_CONFIRMED
```

COD may skip online capture and move `CREATED → ACCEPTED` (or equivalent) under explicit rules.

Terminal states (common):

- `DELIVERED`
- `CANCELLED`
- `FAILED`
- `REFUNDED` (may overlay / follow cancellation)

---

## FOOD_DELIVERY

```text
CREATED
  ↓
PAYMENT_CONFIRMED
  ↓
ACCEPTED          (merchant)
  ↓
PREPARING
  ↓
READY
  ↓
PICKED_UP         (rider)
  ↓
OUT_FOR_DELIVERY
  ↓
DELIVERED
```

### Allowed transitions (V1)

| From | To | Actor |
|------|----|-------|
| `CREATED` | `PAYMENT_PENDING` | system |
| `PAYMENT_PENDING` | `PAYMENT_CONFIRMED` | payments |
| `PAYMENT_PENDING` | `CANCELLED` | customer/system |
| `PAYMENT_CONFIRMED` | `ACCEPTED` | merchant |
| `PAYMENT_CONFIRMED` | `CANCELLED` | merchant/customer (policy) |
| `ACCEPTED` | `PREPARING` | merchant |
| `PREPARING` | `READY` | merchant |
| `READY` | `PICKED_UP` | rider / system |
| `PICKED_UP` | `OUT_FOR_DELIVERY` | rider |
| `OUT_FOR_DELIVERY` | `DELIVERED` | rider |
| `*` (non-terminal) | `CANCELLED` | per cancellation policy |

---

## HYPERLOCAL_DELIVERY

Similar to food; inventory reservation occurs at payment confirmation.

```text
CREATED
  ↓
PAYMENT_CONFIRMED   (+ inventory reserved)
  ↓
ACCEPTED
  ↓
PICKING             (store staff)
  ↓
READY
  ↓
PICKED_UP
  ↓
OUT_FOR_DELIVERY
  ↓
DELIVERED
```

On cancel after reserve: release inventory via stock movement.

---

## COURIER

```text
CREATED
  ↓
PAYMENT_CONFIRMED
  ↓
PICKUP_ASSIGNED
  ↓
PICKED_UP
  ↓
IN_TRANSIT
  ↓
DELIVERED           (+ proof of delivery)
```

No merchant kitchen states. Package metadata lives on order/fulfillment extras JSON, not a separate order type.

---

## Implementation contract

```python
# Pseudocode — do not hardcode FOOD states on Order
class StateMachineRegistry:
    def get(self, profile: str) -> StateMachine: ...

class StateMachine:
    def can_transition(self, from_status: str, to_status: str, context) -> bool: ...
    def transition(self, order, to_status: str, actor, reason=None) -> Order: ...
```

Rules:

1. Reject illegal transitions with a domain error.
2. Persist status history (`order_status_events`) for audit.
3. Emit domain events on successful transitions (`OrderAccepted`, `OrderReady`, …).
4. Fulfillment/delivery statuses are **separate** from order status but must stay consistent via handlers.

---

## Cancellation & refunds

Cancellation policy is config-driven (who can cancel in which state). Refunds are payment-module concerns triggered by events; they do not invent a second order model.
