# Settlements UI (Phase 27)

Admin and merchant surfaces for the ledger-first settlement lifecycle.

## Admin web

| Route | Purpose |
|-------|---------|
| `/settlements` | List with party type + status filters |
| `/settlements/new` | Create period (MERCHANT / RIDER / PLATFORM) |
| `/settlements/[id]` | Detail + lifecycle actions |

**Lifecycle buttons** (admin only):

1. **Calculate** — aggregate unlinked ledger lines for the party
2. **Reconcile** — match payments/refunds vs cash ledger
3. **Approve** — sign off payout
4. **Mark paid** — terminal state

## Merchant PWA

| Route | Purpose |
|-------|---------|
| `/settlements` | Read-only list for selected business |
| `/settlements/[id]` | Read-only detail + report JSON |

Merchants cannot create or transition settlements — they view MERCHANT-party periods scoped to businesses they own.

## Backend scoping

`GET /settlements` and `GET /settlements/{id}` auto-scope for `BUSINESS_OWNER` / `BUSINESS_MANAGER` users:

- Only `party_type=MERCHANT`
- Only `party_id` in their role bindings
- Cross-business access returns 404

## Shared UI

`SettlementCard` in `@commerce/ui` — status badge, total, period, ledger entry count.

## api-client

`listSettlements`, `getSettlement`, `createSettlement`, `calculateSettlement`, `reconcileSettlement`, `approveSettlement`, `markSettlementPaid`, `listOrderSettlements`

## Demo flow

1. Run a delivered COD order (food or grocery)
2. **Admin** (:3003) → Settlements → New → MERCHANT + Spice Kitchen → Create
3. Open detail → Calculate → Reconcile → Approve → Mark paid
4. **Merchant** (:3001) → Settlements → view the same period (read-only)

## API version

`0.27.0`
