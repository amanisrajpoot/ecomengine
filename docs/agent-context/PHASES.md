# Pending phases — files to open (not the whole tree)

Source of sequence: `docs/milestones.md` headings. **Do not read that file** unless you are changing phase order.

Checkout now: **Phase 15 done**. Implement **Phase 16** next ([STATE.md](./STATE.md)).

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

**Status:** implemented (v0.6.0).

- `tax_rules` with CGST/SGST/IGST codes, categories, kinds, payer
- Platform default rules seeded; tenant overrides supported
- `POST /tax/calculate` + pricing pipeline integration
- Alembic `phase6_tax`

**Read:** `docs/tax-engine.md`; SCHEMA tax (~371–390)

**Write:** (done) `taxation/*`, `test_phase6_tax.py`, types + api-client

---

## Phase 7 — Orders

**Status:** implemented (v0.7.0).

- Universal `Order` + frozen items + pricing snapshot
- Configurable profiles: FOOD_DELIVERY, HYPERLOCAL_DELIVERY, COURIER
- Checkout from cart; `order_status_events` audit trail
- Alembic `phase7_orders`

**Read:** `docs/order-state-machines.md`; domain-model Order (~175–192); SCHEMA orders (~290–334)

**Write:** (done) `orders/*`, `test_phase7_orders.py`, types + api-client

---

## Phase 8 — Payments

**Status:** implemented (v0.8.0).

- `PaymentGateway` interface; COD auto-capture; Razorpay stub
- Idempotency-Key on payment create
- Refunds; order → `PAYMENT_CONFIRMED` on capture
- Alembic `phase8_payments`

**Read:** domain-model Payments (~194–203); SCHEMA payments (~336–369); api-conventions Idempotency

**Write:** (done) `payments/*`, `test_phase8_payments.py`, types + api-client

---

## Phase 9 — Ledger

**Status:** implemented (v0.9.0).

- Immutable `ledger_entries` with `event_group_id`, balanced postings
- Post on `PAYMENT_CAPTURED` (payment capture hook)
- Refund reversal postings on `REFUND_COMPLETED`
- Alembic `phase9_ledger`

**Read:** `docs/settlement-engine.md` § LedgerEntry (~41–60); SCHEMA ledger (~394–410)

**Write:** (done) `ledger/*`, `test_phase9_ledger.py`, types + api-client

---

## Phase 10 — Settlements

**Status:** implemented (v0.10.0).

- Aggregate unsettled ledger lines by party (MERCHANT, DELIVERY_PARTNER, PLATFORM)
- `settlement_ledger_links` — one settlement link per ledger entry
- Lifecycle: CALCULATED → RECONCILED → APPROVED → PAID
- Alembic `phase10_settlements`

**Read:** rest of `docs/settlement-engine.md`; SCHEMA settlements (~412–434)

**Write:** (done) `settlements/*`, `test_phase10_settlements.py`, types + api-client

---

## Phase 11 — Fulfillment

**Status:** implemented (v0.11.0).

- `fulfillments` one per order (unique `order_id`)
- Types: DELIVERY, PICKUP, SELF_PICKUP, SCHEDULED, MULTI_STOP
- Auto-create on checkout; lifecycle PENDING → ACTIVE → COMPLETED
- Alembic `phase11_fulfillment`

**Read:** `docs/fulfillment.md` through Fulfillment types; SCHEMA fulfillments (~438–449)

**Write:** (done) `fulfillment/*`, `test_phase11_fulfillment.py`, types + api-client

---

## Phase 12 — Delivery

**Status:** implemented (v0.12.0).

- `delivery_partner_profiles`, `vehicles`, `deliveries`, `delivery_stops`
- Assignment V1: nearest online partner to pickup
- Stop completion with proof metadata
- Alembic `phase12_delivery`

**Read:** `docs/fulfillment.md` Delivery + assignment; SCHEMA deliveries/stops (~451–479); SCHEMA partner/vehicle (~78–104)

**Write:** (done) `delivery/*`, `partners/*`, `test_phase12_delivery.py`, types + api-client

---

## Phase 13 — Food golden path

**Status:** implemented (tests only).

- E2E: FOOD catalog+addons → cart → COD pay → kitchen FSM → rider delivery → ledger → settlement
- No `FoodOrder` table — uses universal `Order`

**Read:** order-state-machines FOOD (~43–79); pricing-engine Food example; fulfillment vertical mapping

**Write:** (done) `test_phase13_food_golden.py`

---

## Phase 14 — Hyperlocal

**Status:** implemented (v0.14.0).

- Inventory reserve on `PAYMENT_CONFIRMED` for `HYPERLOCAL_DELIVERY`
- Consume on `DELIVERED`, release on `CANCELLED`
- Golden path test with GROCERY inventory

**Read:** order-state-machines HYPERLOCAL; inventory reserve/consume; pricing Hyperlocal

**Write:** (done) `inventory/order_hooks.py`, `test_phase14_hyperlocal.py`

---

## Phase 15 — Courier

**Status:** implemented (v0.15.0).

- `POST /courier/quote` — base + distance + weight + vehicle + express
- Courier cart lines (`line_type: COURIER_QUOTE`) without catalog
- Golden path: quote → pay → `PICKUP_ASSIGNED` → rider POD → settlement

**Read:** order-state-machines COURIER; pricing Courier; fulfillment courier mapping

**Write:** (done) `pricing/courier.py`, `pricing/router.py`, `test_phase15_courier.py`, types + api-client

---

## Phase 16 — Experience apps

**Status:** Customer PWA implemented (`apps/customer-pwa`).

| Phase | App | Start files |
|-------|-----|-------------|
| 16 | `apps/customer-pwa` | (done) routes under `app/`, `components/AppShell.tsx`, `lib/api.ts` |
| 17 | `apps/merchant-pwa` | (done) store dashboard, orders, catalog, `lib/orderTransitions.ts` |
| 18 | `apps/rider-pwa` | same pattern |
| 19 | `apps/admin-web` | same pattern |

Plus `packages/ui`, `packages/api-client`, `packages/types` as ROUTES.md says.

---

## Phase 20 — ONDC

**Read:** `docs/architecture.md` adapters (~25–35, exclusions)

**Write:** `backend/app/integrations/ondc/` only — core modules must not import ONDC

---

When a phase ships: set [STATE.md](./STATE.md) to the next phase; mark MAP modules non-empty; do not copy this file into chat.
