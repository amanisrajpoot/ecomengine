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

**Status:** implemented in backend (JWT, OTP + password, tenants, platform config, role bindings, thin `Business` model for config/RBAC scope).

## Phase 2 — Business & location

- Business onboarding
- Types as capabilities (`FOOD`, `RETAIL`, `GROCERY`, `COURIER`)
- Locations, hours, geo

**Status:** implemented — business CRUD, capability presets/overrides, location CRUD with India address + hours + service area.

## Phase 3 — Catalog

- Categories, products, variants, addons, bundles, images, availability

**Status:** implemented — generic catalog APIs gated by business capabilities (`catalog`, `addons`).

## Phase 4 — Inventory

- Optional; stock, reserved, movements, low/out of stock

**Status:** implemented — movement-backed stock mutations; `available = on_hand - reserved`; gated by `capabilities.inventory`.

## Phase 5 — Cart + pricing

- Cart aggregate + pricing pipeline + breakdown snapshots

**Status:** implemented — cart CRUD with pricing snapshots; pricing pipeline calls taxation stub (CGST/SGST or IGST). Full TaxRule engine is Phase 6.

## Phase 6 — Tax

- Independent GST engine (customer vs platform vs settlement kinds)

**Status:** implemented — `TaxRule` persistence, India defaults (CGST/SGST/IGST + commission kinds), calculate API; pricing/cart load rules (fallback stub if none).

## Phase 7 — Orders

- Universal order + configurable state machines

**Status:** implemented — checkout from cart, `FOOD_DELIVERY` / `HYPERLOCAL_DELIVERY` / `COURIER` profiles, status history + domain events; single `Order` model.

## Phase 8 — Payments

- Multi-gateway interface (`PaymentGateway` + registry); Cashfree first + COD
- Mock mode when credentials missing / `PAYMENTS_MOCK=true`

**Status:** implemented — initiate / verify / refund / Cashfree webhook; order payment confirmation via payments actor.

## Phase 9 — Ledger

- Financial events → immutable ledger entries (balanced postings)
- Hooks on payment capture / COD authorize / refund; manual adjustments

**Status:** implemented — `ledger_entries`, posting builders, order/account queries, balances API.

## Phase 10 — Settlements

- Merchant / rider / platform lifecycle from ledger aggregation
- Links ledger entries once; reconcile → approve → paid

**Status:** implemented — settlements + settlement_ledger_links; calculate/reconcile/approve/mark-paid APIs.

## Phase 11 — Fulfillment

- Decouple fulfillment from order (1:1 `Fulfillment`; no rider fields on Order)
- Sync projection from order status; logistics remain Phase 12

**Status:** implemented — fulfillments + status events; create at payment confirm; transition API.

## Phase 12 — Delivery

- Partners, vehicles, assignment V1, tracking hooks, stop proof of delivery

**Status:** implemented — delivery_partner_profiles, vehicles, deliveries, delivery_stops; nearest-online assignment; REST tracking.

## Phase 13 — Vertical 1: Food

- End-to-end restaurant → rider → customer → settlement on shared engines
- Order debugger (Order → Payment → Ledger → Fulfillment → Delivery → Settlement)
- Thin `verticals/food` capability preset (no FoodOrder model)

**Status:** implemented — golden-path test + `GET /orders/{id}/debugger` + `seed_food_demo`.

## Phase 14 — Vertical 2: Hyperlocal

- Inventory + store discovery; minimal new core code
- `GET /stores/nearby` (haversine + service_area)
- Reserve on `PAYMENT_CONFIRMED`, consume on `DELIVERED`, release on cancel
- Thin `verticals/hyperlocal` preset (GROCERY/RETAIL; no GroceryOrder model)

**Status:** implemented — golden-path + cancel-release tests + `seed_hyperlocal_demo`.

## Phase 15 — Vertical 3: Courier

- Pickup/drop package flow; proves generic engine
- `POST /courier/quote` — fare from distance + weight + vehicle (+ express)
- `POST /courier/shipments` — shared `Order` (`MULTI_STOP` / `COURIER` profile; no catalog)
- Delivery sync walks courier states: assign → pickup → in-transit → delivered

**Status:** implemented — golden-path test + `seed_courier_demo`.

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
