# Settlement Engine

## Architectural principle

> Never calculate merchant payout by doing one giant formula at settlement time.

Flow:

```text
Order
  ↓
Financial Events
  ↓
Ledger
  ↓
Settlement
```

Every rupee must be auditable via ledger entries.

---

## Example (illustrative)

```text
ORDER #1234

Customer           -₹1,050
Platform           +₹1,050
Tax liability       ₹50
Commission          ₹100
Commission GST      ₹18
Delivery payout     ₹40
Merchant payable    ₹892
```

Exact posting rules are tenant-configurable; the shape is fixed: **event → ledger lines → settlement aggregation**.

---

## LedgerEntry

Immutable.

| Field | Notes |
|-------|-------|
| `id` | UUID |
| `tenant_id` | |
| `order_id` | Nullable for non-order adjustments |
| `event_type` | e.g. `PAYMENT_CAPTURED`, `COMMISSION`, `DELIVERY_PAYOUT` |
| `account` | e.g. `PLATFORM_CASH`, `MERCHANT_PAYABLE`, `TAX_LIABILITY`, `RIDER_PAYABLE` |
| `direction` | `DEBIT` / `CREDIT` |
| `amount_paise` | > 0 |
| `currency` | `INR` |
| `metadata` | JSON |
| `created_at` | UTC |

Prefer balanced postings per financial event (sum debits = sum credits) within an event group id.

### V1 accounts

| Account | Role |
|---------|------|
| `PLATFORM_CASH` | Online payment inflow / refund outflow |
| `CUSTOMER_RECEIVABLE` | COD authorized amount |
| `TAX_LIABILITY` | Customer GST + commission GST |
| `PLATFORM_FEE_REVENUE` | Platform convenience fee |
| `PLATFORM_COMMISSION` | Merchant commission |
| `MERCHANT_PAYABLE` | Net merchant entitlement |
| `RIDER_PAYABLE` | Delivery fee accrual |
| `PLATFORM_CLEARING` | Manual adjustments |

### V1 event types

- `ORDER_PAYMENT_CAPTURED` — posted on Cashfree capture or COD authorize
- `PAYMENT_REFUND` — posted on refund
- `MANUAL_ADJUSTMENT` — admin balanced adjustment

Commission rate defaults to `LEDGER_DEFAULT_COMMISSION_BPS` (1000 = 10%), overridable via tenant `config.commission_bps` / `config.extra.commission_bps`. Commission GST uses `PLATFORM_SERVICE` / `COMMISSION` tax rules when present.

---

## Settlement parties

- Merchant
- Rider (`DELIVERY_PARTNER`)
- Platform

---

## Settlement lifecycle

```text
PENDING
  ↓
CALCULATED
  ↓
RECONCILED
  ↓
APPROVED
  ↓
PAID
```

| Status | Meaning |
|--------|---------|
| `PENDING` | Period open or entries not yet aggregated |
| `CALCULATED` | Totals derived from ledger |
| `RECONCILED` | Checked against payments/refunds |
| `APPROVED` | Ops approved payout |
| `PAID` | Payout executed / marked paid |

---

## Settlement contents

Support inclusion of:

- Commission
- Fees
- Taxes (settlement deductions / platform service tax)
- Refunds
- Adjustments
- Incentives
- Rider earnings
- Merchant payout
- Settlement reports (export later)

---

## APIs (Phase 10)

- `POST /api/v1/settlements` — create period for MERCHANT / RIDER / PLATFORM
- `GET /api/v1/settlements` — list (filter party/status)
- `GET /api/v1/settlements/{id}` — detail with linked ledger entry ids
- `POST /api/v1/settlements/{id}/calculate` — aggregate unlinked ledger lines for party accounts
- `POST /api/v1/settlements/{id}/reconcile` — check payments/refunds vs cash ledger for included orders
- `POST /api/v1/settlements/{id}/approve` / `mark-paid`
- `GET /api/v1/orders/{id}/settlements` — settlements touching an order

**Party conventions (V1):**
- `MERCHANT` → `party_id` = `business_id`; account `MERCHANT_PAYABLE`
- `RIDER` → `party_id` = rider bucket id; account `RIDER_PAYABLE` (assignment in Phase 12)
- `PLATFORM` → `party_id` = `tenant_id`; accounts `PLATFORM_COMMISSION` + `PLATFORM_FEE_REVENUE`

Each ledger entry links to at most one settlement (`settlement_ledger_links.ledger_entry_id` unique).

Admin **order debugger** must show Order → … → Ledger → Settlement for any order.
