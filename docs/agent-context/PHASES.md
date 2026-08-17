# Pending phases — files to open (not the whole tree)

Source of sequence: `docs/milestones.md` headings. **Do not read that file** unless you are changing phase order.

Checkout now: **Phase 5 done**. Implement **Phase 6** next ([STATE.md](./STATE.md)).

Each phase lists **read** (specs, with schema slice) and **write** (create/edit). Skip later phases.

---

## Phase 1 — Platform foundation

**Status:** implemented (v0.1.0).

- Auth: OTP, email/password, JWT, bootstrap super admin
- Identity + RBAC (`user_role_bindings`)
- Tenants + `platform_config`
- Alembic `phase1_foundation` migration

**Read:** `docs/permissions.md`; `docs/api-conventions.md`; SCHEMA tenancy + identity

**Write:** (done) `identity/*`, `tenants/*`, `core/deps.py`, `tests/test_phase1_foundation.py`

---

## Phase 2 — Business & location

**Status:** implemented (v0.2.0).

- Business CRUD with type presets (`FOOD`, `GROCERY`, `RETAIL`, `COURIER`)
- Capability defaults per type; `BUSINESS_OWNER` on create
- Nested locations with hours, geo, service area
- Alembic `phase2_business_location`

**Read:** `docs/domain-model.md` § Business & location (~64–92); SCHEMA businesses (~106–142)

**Write:** (done) `businesses/*`, `locations/*`, `test_phase2_business_location.py`, types + api-client

---

## Phase 3 — Catalog

**Status:** implemented (v0.3.0).

- Categories (hierarchical), products, variants (paise prices)
- Addons + product links (gated by `capabilities.addons`)
- Bundles/combos with variant items
- Alembic `phase3_catalog`

**Read:** domain-model Catalog (~94–141); SCHEMA catalog (~144–223)

**Write:** (done) `catalog/*`, `test_phase3_catalog.py`, types + api-client

---

## Phase 4 — Inventory

**Status:** implemented (v0.4.0).

- Optional per business (`capabilities.inventory`)
- `on_hand`, `reserved`, `available`, low-stock threshold
- Every mutation records a `stock_movements` row
- Reserve / release / adjust APIs
- Alembic `phase4_inventory`

**Read:** domain-model Inventory (~143–156); SCHEMA inventory (~225–260)

**Write:** (done) `inventory/*`, `test_phase4_inventory.py`, types + api-client

---

## Phase 5 — Cart + pricing

**Status:** implemented (v0.5.0).

- Cart + cart_items with variant/bundle lines and addons
- Pricing pipeline → `PriceBreakdown` (tax stub until Phase 6)
- `pricing_snapshot` on cart; customer-scoped RBAC
- Alembic `phase5_cart`

**Read:** `docs/pricing-engine.md`; domain-model Cart (~158–173); SCHEMA carts (~262–288)

**Write:** (done) `cart/*`, `pricing/*`, `test_phase5_cart_pricing.py`, types + api-client

---

## Phase 6 — Tax

**Read:** `docs/tax-engine.md`; SCHEMA tax (~371–390)

**Write:** `backend/app/taxation/*`; `test_phase6_*.py`

---

## Phase 7 — Orders

**Read:** `docs/order-state-machines.md`; domain-model Order (~175–192); SCHEMA orders (~290–334)

**Write:** `backend/app/orders/*`; `test_phase7_*.py`

---

## Phase 8 — Payments

**Read:** domain-model Payments (~194–203); SCHEMA payments (~336–369); api-conventions Idempotency

**Write:** `backend/app/payments/*` (gateway interface + COD + Razorpay later); `test_phase8_*.py`

---

## Phase 9 — Ledger

**Read:** `docs/settlement-engine.md` § LedgerEntry (~41–60); SCHEMA ledger (~394–410)

**Write:** `backend/app/ledger/*`; `test_phase9_*.py`

---

## Phase 10 — Settlements

**Read:** rest of `docs/settlement-engine.md`; SCHEMA settlements (~412–434)

**Write:** `backend/app/settlements/*`; `test_phase10_*.py`

---

## Phase 11 — Fulfillment

**Read:** `docs/fulfillment.md` through Fulfillment types; SCHEMA fulfillments (~438–449)

**Write:** `backend/app/fulfillment/*`; `test_phase11_*.py`

---

## Phase 12 — Delivery

**Read:** `docs/fulfillment.md` Delivery + assignment; SCHEMA deliveries/stops (~451–479); SCHEMA partner/vehicle (~78–104)

**Write:** `backend/app/delivery/*`; `backend/app/partners/*`; `test_phase12_*.py`

---

## Phase 13 — Food golden path

**Read:** order-state-machines FOOD (~43–79); pricing-engine Food example; fulfillment vertical mapping

**Write:** tests `test_phase13_food*.py` wiring existing engines — **no FoodOrder table**

---

## Phase 14 — Hyperlocal

**Read:** order-state-machines HYPERLOCAL; inventory reserve/consume; pricing Hyperlocal

**Write:** `test_phase14_*.py` — inventory capability on GROCERY/RETAIL

---

## Phase 15 — Courier

**Read:** order-state-machines COURIER; pricing Courier; fulfillment courier mapping

**Write:** `test_phase15_*.py` + any courier quote helpers in pricing/delivery

---

## Phases 16–19 — Experience apps

**Write under only the named app:**

| Phase | App | Start files |
|-------|-----|-------------|
| 16 | `apps/customer-pwa` | `app/page.tsx`, new routes under `app/` |
| 17 | `apps/merchant-pwa` | same pattern |
| 18 | `apps/rider-pwa` | same pattern |
| 19 | `apps/admin-web` | same pattern |

Plus `packages/ui`, `packages/api-client`, `packages/types` as ROUTES.md says.

---

## Phase 20 — ONDC

**Read:** `docs/architecture.md` adapters (~25–35, exclusions)

**Write:** `backend/app/integrations/ondc/` only — core modules must not import ONDC

---

When a phase ships: set [STATE.md](./STATE.md) to the next phase; mark MAP modules non-empty; do not copy this file into chat.
