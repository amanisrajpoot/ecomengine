# Ledger UI (Phase 30)

Expose Phase 9 immutable ledger APIs in admin and merchant experience apps.

## Admin web

| Route | Purpose |
|-------|---------|
| `/ledger` | Tenant-wide entry list with account/event/order filters + balances |
| `/ledger/events/[eventGroupId]` | Event group detail with per-account totals |
| `/ledger/adjustments/new` | Manual balanced adjustment form (`ledger.adjust`) |
| Order debugger | `OrderLedgerPanel` replaces raw ledger JSON blocks |

## Merchant PWA

| Route | Purpose |
|-------|---------|
| `/ledger` | Read-only entries + balances for selected business |
| Order detail | Per-order ledger panel |

## Backend scoping

`GET /ledger/entries`, `GET /ledger/balances`, and `GET /orders/{id}/ledger` (`ledger.read`):

- **Merchants** (`BUSINESS_OWNER` / `BUSINESS_MANAGER`) — auto-scoped to owned businesses via order `business_id`
- **Admins** — tenant-wide; optional `business_id` filter

`POST /ledger/adjustments` remains admin-only (`ledger.adjust`).

## Shared UI

- `LedgerEntryCard` — account, direction, amount, event type, reference
- `LedgerBalancesPanel` — debit/credit/net per account
- `OrderLedgerPanel` — grouped entries + optional balances for one order

## api-client

`listLedgerEntries`, `getOrderLedger`, `getLedgerEvent`, `listLedgerBalances`, `createLedgerAdjustment`

## Demo flow

1. Deliver a COD food order so `ORDER_PAYMENT_CAPTURED` postings exist
2. **Admin** (:3003) → Ledger → filter `MERCHANT_PAYABLE`
3. Open order debugger → Ledger panel → link to event group
4. **Merchant** (:3001) → Ledger → select Spice Kitchen → view business-scoped entries
5. **Admin** → Settlements → Calculate — links the same ledger lines

## API version

`0.30.0`
