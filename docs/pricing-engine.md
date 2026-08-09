# Pricing Engine

## Role

Dedicated pricing pipeline. Every calculation returns a **price breakdown**, never only a total.

Money unit: **integer paise (INR)**.

---

## Pipeline

```text
Items
 ↓
Base Price
 ↓
Modifiers (addons / variants extras)
 ↓
Discounts (promotions)
 ↓
Delivery Fee
 ↓
Platform Fee
 ↓
Other Fees
 ↓
Tax
 ↓
Final Total
```

Order of operations is fixed unless a tenant config explicitly documents a variant (prefer not to).

---

## Breakdown contract

```json
{
  "currency": "INR",
  "subtotal_paise": 50000,
  "discount_paise": 5000,
  "delivery_fee_paise": 3000,
  "platform_fee_paise": 500,
  "other_fees_paise": 0,
  "tax_paise": 2500,
  "tax_lines": [
    {
      "code": "CGST",
      "rate_bps": 250,
      "amount_paise": 1250
    },
    {
      "code": "SGST",
      "rate_bps": 250,
      "amount_paise": 1250
    }
  ],
  "total_paise": 51000,
  "lines": []
}
```

Field rules:

| Field | Meaning |
|-------|---------|
| `*_paise` | Integer; never float |
| `rate_bps` | Basis points (250 = 2.5%) |
| `lines` | Optional per-item breakdown |
| `tax_lines` | From tax engine; do not invent “GST” as a single opaque number when components exist |

Invariant:

```text
total_paise =
  subtotal_paise
  - discount_paise
  + delivery_fee_paise
  + platform_fee_paise
  + other_fees_paise
  + tax_paise   # when tax is exclusive
```

For tax-inclusive catalog prices, document inclusive handling in [tax-engine.md](./tax-engine.md); breakdown must still surface tax components.

---

## Inputs

- Cart or quote request: items (variant_id, qty, addons), business, location, customer location, fulfillment type, promo codes
- Business / tenant fee configs
- Delivery fee quote from delivery module (or pricing rules)
- Tax calculation from taxation module

Pricing **calls** tax; it does not embed GST logic.

---

## Outputs

- `PriceBreakdown` value object
- Persisted on cart (`pricing_snapshot`) and frozen on order at checkout

---

## Vertical examples

### Food

Base variant + addon modifiers + delivery + platform fee + GST on applicable components.

### Hyperlocal

Same pipeline; inventory does not change pricing math.

### Courier

Often no catalog subtotal; “items” may be a service quote:

```text
base_fare + distance + weight + vehicle + express_surcharge
```

Still emitted as the same breakdown shape (`subtotal_paise` = fare components sum, etc.).

---

## Non-goals (V1)

- Dynamic surge pricing
- Personalized AI pricing
- Multi-currency
