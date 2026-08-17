# Milestones

Dependency order matters more than calendar duration. Implement sequentially.

## Phase 0 — Spec + scaffold (this PR)

- Docs in `/docs`
- Monorepo + Docker Compose + FastAPI health + Next app shells

## Phase 1 — Platform foundation

- Auth: OTP, email/password (social later)
- Identity + RBAC
- Multi-tenancy (`tenant_id`)
- `PlatformConfig` / `TenantConfig` / `BusinessConfig`

**Status:** implemented (API `0.1.0`, alembic `phase1_foundation`).

## Phase 2 — Business & location

- Business onboarding
- Types as capabilities (`FOOD`, `RETAIL`, `GROCERY`, `COURIER`)
- Locations, hours, geo

**Status:** implemented (API `0.2.0`, alembic `phase2_business_location`).

## Phase 3 — Catalog

- Categories, products, variants, addons, bundles, images, availability

**Status:** implemented (API `0.3.0`, alembic `phase3_catalog`).

## Phase 4 — Inventory

- Optional; stock, reserved, movements, low/out of stock

**Status:** implemented (API `0.4.0`, alembic `phase4_inventory`).

## Phase 5 — Cart + pricing

- Cart aggregate + pricing pipeline + breakdown snapshots

**Status:** implemented (API `0.5.0`, alembic `phase5_cart`).

## Phase 6 — Tax

- Independent GST engine (customer vs platform vs settlement kinds)

**Status:** implemented (API `0.6.0`, alembic `phase6_tax`).

## Phase 7 — Orders

- Universal order + configurable state machines

**Status:** implemented (API `0.7.0`, alembic `phase7_orders`).

## Phase 8 — Payments

- Gateway interface; Razorpay + COD

**Status:** implemented (API `0.8.0`, alembic `phase8_payments`).

## Phase 9 — Ledger

- Financial events → immutable ledger entries

**Status:** implemented (API `0.9.0`, alembic `phase9_ledger`).

## Phase 10 — Settlements

- Merchant / rider / platform lifecycle

**Status:** implemented (API `0.10.0`, alembic `phase10_settlements`).

## Phase 11 — Fulfillment

- Decouple fulfillment from order

**Status:** implemented (API `0.11.0`, alembic `phase11_fulfillment`).

## Phase 12 — Delivery

- Partners, vehicles, assignment V1, tracking hooks

**Status:** implemented (API `0.12.0`, alembic `phase12_delivery`).

## Phase 13 — Vertical 1: Food

- End-to-end restaurant → rider → customer → settlement

**Status:** implemented (`test_phase13_food_golden.py`).

## Phase 14 — Vertical 2: Hyperlocal

- Inventory + store discovery; minimal new core code

**Status:** implemented (API `0.14.0`, `test_phase14_hyperlocal.py`).

## Phase 15 — Vertical 3: Courier

- Pickup/drop package flow; proves generic engine

**Status:** implemented (API `0.15.0`, `test_phase15_courier.py`).

## Phases 16–19 — Experience apps

- **Phase 16:** Customer PWA — browse, cart, checkout, orders, courier quote (`apps/customer-pwa`)
- **Phase 17:** Merchant PWA — stores, orders, catalog (`apps/merchant-pwa`)
- **Phase 18:** Rider PWA — jobs, POD, partner profile (`apps/rider-pwa`)
- Phase 19: Admin (incl. order debugger)

## Phase 20 — ONDC adapter

- Only after internal order/fulfillment works; adapters under `integrations/ondc`

---

## MVP definition

MVP is complete only when all three golden flows work on the **same** engines:

### Food

Customer → Restaurant → Rider → Customer → Settlement

### Hyperlocal

Customer → Store → Inventory → Rider → Customer → Settlement

### Courier

Customer → Pickup → Rider → Drop → Settlement

Shared systems required:

- User, Business, Catalog concepts, Cart (where applicable)
- Pricing, Tax, Payment, Order, Ledger, Settlement, Delivery

---

## Acceptance tests (golden)

Automated integration tests should eventually encode:

1. **Food** — create business (FOOD) → catalog with addons → cart → pay → accept → prepare → ready → assign rider → deliver → ledger → settlement
2. **Hyperlocal** — inventory enabled → reserve on pay → pick → deliver → release/consume stock → settlement
3. **Courier** — quote by distance/weight/vehicle → pay → assign → pickup → transit → POD → settlement
