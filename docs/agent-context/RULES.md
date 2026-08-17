# Invariants (short)

Full text: `docs/coding-conventions.md`. Stop if a change violates these.

1. **One `Order` model** — never `FoodOrder` / `GroceryOrder` / `CourierOrder`.
2. **Business `type` is capabilities** — it does not fork the schema.
3. **Money is integer paise** — fields `*_paise`; never floats.
4. **Ledger before settlement** — no one-shot payout formula.
5. **ONDC is an adapter** — core must not import ONDC types.

## Layout

- Backend domain only in `backend/app/<module>/` (models, schemas, service, router).
- Routers stay thin. Shared TS types in `packages/types`; HTTP in `packages/api-client`; UI in `packages/ui`.
- Tenant filter on every tenant-owned query.

## IDs / time

- UUID v4 PKs. Persist UTC `timestamptz`. Default business TZ `Asia/Kolkata`.

## Tests

- Exact integer money. Golden flows later: Food, Hyperlocal, Courier on the **same** engines.
