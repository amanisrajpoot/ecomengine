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

## Phase 4 — Inventory

- Optional; stock, reserved, movements, low/out of stock

## Phase 5 — Cart + pricing

- Cart aggregate + pricing pipeline + breakdown snapshots

## Phase 6 — Tax

- Independent GST engine (customer vs platform vs settlement kinds)

## Phase 7 — Orders

- Universal order + configurable state machines

## Phase 8 — Payments

- Gateway interface; Razorpay + COD

## Phase 9 — Ledger

- Financial events → immutable ledger entries

## Phase 10 — Settlements

- Merchant / rider / platform lifecycle

## Phase 11 — Fulfillment

- Decouple fulfillment from order

## Phase 12 — Delivery

- Partners, vehicles, assignment V1, tracking hooks

## Phase 13 — Vertical 1: Food

- End-to-end restaurant → rider → customer → settlement

## Phase 14 — Vertical 2: Hyperlocal

- Inventory + store discovery; minimal new core code

## Phase 15 — Vertical 3: Courier

- Pickup/drop package flow; proves generic engine

## Phases 16–19 — Experience apps

- Customer PWA, Merchant PWA, Rider PWA, Admin (incl. order debugger)

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
