# Agent context index (dispatcher)

**Start here. Then `STATE.md`. Then one table below. Do not Glob the repo. Do not read all of `docs/`.**

If a path is missing after you add it, **register it in [MAP.md](./MAP.md) in the same PR** so the next session does not scan.

| Step | File | When |
|------|------|------|
| 1 | [INDEX.md](./INDEX.md) | This dispatcher |
| 2 | [STATE.md](./STATE.md) | Phase, version, next work |
| 3a | [PHASES.md](./PHASES.md) | Implementing the **next numbered phase** |
| 3b | [ROUTES.md](./ROUTES.md) | A **kind of change** (endpoint, table, PWA page, …) |
| 3c | [MAP.md](./MAP.md) | Jump to a **module’s files** (no tree walk) |
| 3d | [SCHEMA.md](./SCHEMA.md) | `docs/schema.md` **line ranges** only |
| 3e | [RULES.md](./RULES.md) | Invariants |
| 3f | [PROTOCOL.md](./PROTOCOL.md) | Token rules |

## Domain → open these (nothing else)

| Domain | Spec (offset) | Schema slice | Code dir | Tests (when present) |
|--------|---------------|--------------|----------|----------------------|
| Auth / users / RBAC | `docs/permissions.md`; `docs/api-conventions.md` Auth | [SCHEMA.md](./SCHEMA.md) identity | `backend/app/identity/` | `backend/tests/test_phase1*.py` |
| Tenants / config | `docs/api-conventions.md` Tenancy | SCHEMA tenancy | `backend/app/tenants/` + `backend/app/core/config.py` | same Phase 1 tests |
| Business | `docs/domain-model.md` § Business | SCHEMA businesses | `backend/app/businesses/` | `test_phase2*.py` |
| Locations / hours | `docs/domain-model.md` § BusinessLocation | SCHEMA `business_locations` | `backend/app/locations/` | `test_phase2*.py` |
| Catalog / addons | `docs/domain-model.md` § Catalog | SCHEMA catalog | `backend/app/catalog/` | `test_phase3*.py` |
| Inventory | `docs/domain-model.md` § Inventory | SCHEMA inventory | `backend/app/inventory/` | `test_phase4*.py` |
| Cart | `docs/domain-model.md` § Cart | SCHEMA carts | `backend/app/cart/` | `test_phase5*.py` |
| Pricing | `docs/pricing-engine.md` | — | `backend/app/pricing/` | `test_phase5*.py` |
| GST / tax | `docs/tax-engine.md` | SCHEMA tax | `backend/app/taxation/` | `test_phase6*.py` |
| Orders / FSM | `docs/order-state-machines.md` | SCHEMA orders | `backend/app/orders/` | `test_phase7*.py` |
| Payments | `docs/domain-model.md` § Payments | SCHEMA payments | `backend/app/payments/` | `test_phase8*.py` |
| Ledger | `docs/settlement-engine.md` § LedgerEntry | SCHEMA ledger | `backend/app/ledger/` | `test_phase9*.py` |
| Settlements | `docs/settlement-engine.md` | SCHEMA settlements | `backend/app/settlements/` | `test_phase10*.py` |
| Fulfillment | `docs/fulfillment.md` § Separation | SCHEMA fulfillments | `backend/app/fulfillment/` | `test_phase11*.py` |
| Delivery / tracking | `docs/fulfillment.md` § Delivery | SCHEMA deliveries | `backend/app/delivery/` | `test_phase12*.py` |
| Riders / vehicles | `docs/fulfillment.md` § Partner | SCHEMA identity partners | `backend/app/partners/` | `test_phase12*.py` |
| Promotions | `docs/schema.md` promotions stub | SCHEMA promotions | `backend/app/promotions/` | later |
| Notifications | — | — | `backend/app/notifications/` | later |
| Support / debugger | — | — | `backend/app/support/` | later |
| Reviews | — | — | `backend/app/reviews/` | later |
| ONDC adapter | `docs/architecture.md` adapters | — | `backend/app/integrations/` | Phase 20 |
| Shared TS types | — | — | `packages/types/src/index.ts` | `pnpm typecheck` |
| HTTP client | — | — | `packages/api-client/src/index.ts` | typecheck |
| Shared UI | — | — | `packages/ui/src/` | typecheck |
| Customer app | — | — | `apps/customer-pwa/` | typecheck |
| Merchant app | — | — | `apps/merchant-pwa/` | typecheck |
| Rider app | — | — | `apps/rider-pwa/` | typecheck |
| Admin app | — | — | `apps/admin-web/` | typecheck |
| Docker / env | `docs/architecture.md` Deployment | — | `docker-compose.yml`, `.env.example` | compose up |

## Grep instead of scan

Run Grep **inside the MAP path**, never `**/*` from repo root.

| Looking for | Grep | Path |
|-------------|------|------|
| HTTP route | `APIRouter` or `@router.` | `backend/app/<module>/` |
| Permission string | `require_permission` or `PERMISSIONS` | `backend/app/identity/` `backend/app/core/` |
| ORM table | `__tablename__` | `backend/app/<module>/models.py` |
| Client method | `request<` | `packages/api-client/src/index.ts` |
| UI export | `export {` | `packages/ui/src/index.ts` |
| App page | `page.tsx` | `apps/<app>/app/` |

## Do not

- Glob the workspace to “see what exists” — use [MAP.md](./MAP.md)
- Read `docs/schema.md` whole — use [SCHEMA.md](./SCHEMA.md) offsets
- Read `docs/milestones.md` whole — use [PHASES.md](./PHASES.md)
- Recap all phases in chat
