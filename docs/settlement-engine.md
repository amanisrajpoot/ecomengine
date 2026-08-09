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

## APIs (future phases)

- List settlements by party
- Settlement detail with linked ledger entry ids
- Approve / mark paid (admin)

Admin **order debugger** must show Order → … → Ledger → Settlement for any order.
