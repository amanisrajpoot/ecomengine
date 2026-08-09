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

- **Phase 16** — Customer PWA: browse nearby Food/Grocery, cart COD checkout, courier quote/book, orders
- **Phase 17** — Merchant PWA: business order queue, accept → prepare/pick → ready transitions
- **Phase 18** — Rider PWA: go online, assigned jobs, stop POD, tracking pings
- **Phase 19** — Admin web: tenant list, order list, full-chain order debugger UI

**Phase 16 status:** implemented — Customer PWA screens + `catalog.read` / food discovery for customers.

**Phase 17 status:** implemented — Merchant PWA kitchen queue + order transitions.

**Phase 18 status:** implemented — Rider PWA + `GET /deliveries?mine=true` + partner `/me` endpoints.

**Phase 19 status:** implemented — Admin web (violet ops shell) + `listTenants` / `getOrderDebugger` in api-client.

## Phase 20 — ONDC adapter

- Beckn BPP ingress under `integrations/ondc` (search → confirm on shared engines)
- `ondc_sessions` links transaction → cart/order; mock mode + callback log
- Core domain unchanged — adapter only

**Status:** implemented — golden-path test + `docs/ondc.md`.

## Phase 21 — Notifications

- Event bus fan-out on order lifecycle (`OrderCreated`, `PaymentCaptured`, …)
- `sms_mock` channel adapter; `notifications` persistence + list API
- Phone from order metadata / payment / customer user

**Status:** implemented — golden test + `docs/notifications.md`.

## Phase 22 — Demo data & local testing

- Unified `seed_demo` — one tenant (`commerce-demo`) with Food + Grocery + Courier + demo users
- Auto-runs in Docker backend startup; `pnpm demo:seed` for local API
- `docs/demo.md` — how to test all four PWAs end-to-end

**Status:** implemented — `seed_demo` + demo guide.

## Phase 23 — Experience polish

- Shared `@commerce/ui`: `Spinner`, `EmptyState`, `StatusBadge`, `PriceBreakdown`, `OrderStatusStepper`
- Customer PWA: env tenant ID, phone on checkout, cart qty/remove, addon picker, order polling + stepper, cart badge
- Merchant PWA: kitchen board cards, auto-refresh queue, status stepper on order detail
- Rider PWA: availability panel, job cards, step-by-step POD flow
- Admin web: dashboard counts, collapsible debugger sections, tenant ID copy/remember

**Status:** implemented — `docs/experience.md`.

## Phase 24 — Dispatch & logistics

- Auto-dispatch on `OrderReady` (food/hyperlocal) and `PaymentCaptured` (courier)
- `DispatchPanel` in `@commerce/ui` — request/retry rider from merchant + admin
- Admin dispatch board (`/dispatch`)
- api-client: `createDelivery`, `assignDelivery`, `getFulfillmentDelivery`, `listDeliveryPartners`
- RBAC: `BUSINESS_OWNER` may assign deliveries

**Status:** implemented — `docs/dispatch.md`.

## Phase 25 — Customer journey

- Delivery address at checkout → `metadata.drop` for fulfillment/delivery stops
- Customer-scoped order list + 404 on cross-customer reads
- `OrderTrackingPanel` on customer order detail (fulfillment + delivery polling)
- Customer cancel for early order statuses
- Courier PWA: editable pickup/drop address fields
- api-client: `listOrders({ mine })`, `transitionOrder` respects `actor`

**Status:** implemented — `docs/customer-journey.md`.

## Phase 26 — Inventory merchant UI

- Merchant PWA stock board (`/inventory`) with business/location filters and low/OOS chips
- Item detail: receive/adjust stock + movement history
- New item flow: link catalog variant to location
- api-client: inventory + `listLocations` methods; `locations.read` RBAC for STAFF
- Demo: `merchant@demo.com` also owns FreshMart grocery

**Status:** implemented — `docs/inventory-merchant.md`.

## Phase 27 — Settlements UI

- Admin web: settlements list, create period, lifecycle actions (calculate → reconcile → approve → mark paid)
- Merchant PWA: read-only settlements for owned businesses
- `SettlementCard` in `@commerce/ui`
- api-client settlement methods; merchant-scoped `GET /settlements`
- Backend: merchant settlement access scoping

**Status:** implemented — `docs/settlements-ui.md`.

## Phase 28 — Online payments UI

- Customer PWA: COD vs Cashfree at checkout; `PaymentPanel` on order detail (mock pay + Cashfree link)
- Admin debugger: verify capture + full refund actions
- api-client: payment list/verify/refund methods
- Backend: customer order scoping on payment routes

**Status:** implemented — `docs/payments-ui.md`.

## Phase 29 — Notifications UI

- Admin: `/notifications` tenant-wide list + order debugger feed
- Customer: `/notifications` + per-order feed on order detail
- Merchant: `/notifications` tenant-wide (business owner roles)
- `NotificationCard` + `OrderNotificationsPanel` in `@commerce/ui`
- api-client: `listNotifications`

**Status:** implemented — `docs/notifications-ui.md`.

## Phase 30 — Ledger UI

- Admin: `/ledger` list + balances, event detail, manual adjustment form
- Merchant: read-only `/ledger` + per-order panel on order detail
- `LedgerEntryCard`, `LedgerBalancesPanel`, `OrderLedgerPanel` in `@commerce/ui`
- api-client ledger methods; merchant scoping on ledger routes
- Order debugger uses structured ledger panel instead of JSON blocks

**Status:** implemented — `docs/ledger-ui.md`.

## Phase 31 — Rider ops UI

- Rider PWA: `/notifications` (Alerts) + `/settlements` (Earnings) read-only
- Backend: rider scoping on notifications (assigned order ids) and settlements (RIDER party)
- RBAC: `DELIVERY_PARTNER` on `notifications.read` and `settlements.read`

**Status:** implemented — `docs/rider-ops-ui.md`.

## Phase 32 — ONDC ops UI

- Admin: `/ondc` session list + adapter meta, `/ondc/[id]` detail with callback log
- `OndcSessionCard` in `@commerce/ui`
- api-client: `getOndcMeta`, `listOndcSessions`, `getOndcSession`
- Backend: `GET /integrations/ondc/sessions` (`ondc.read`)

**Status:** implemented — `docs/ondc-ops-ui.md`.

## Phase 33 — UI foundation + live notifications

- `@commerce/ui`: Toast, Modal, Skeleton, Badge, ErrorState, LiveIndicator, `usePolling`, `useNotificationFeed`, `NotificationFeed`, `NavNotificationBadge`
- All four apps: `ToastProvider` in `AppShell`, nav unread badges on Alerts/Notifications
- Notification pages: live polling (10s), mark-seen on visit, skeleton loaders
- `OrderNotificationsPanel`: 5s polling on order detail
- Merchant kitchen board: new-order toast on poll

**Status:** implemented — `docs/ui-foundation.md`.

## Docker full-stack deploy

- `docker-compose.prod.yml` — API + Postgres + Redis + MinIO + all four PWAs
- `Dockerfile.frontend` — shared multi-stage build for Next.js apps
- `docs/deploy.md` — one-command deploy (Oracle Free Tier, any VPS)

## Phase 34 — Merchant catalog UI

- Merchant PWA: `/catalog`, `/catalog/new`, `/catalog/[productId]`
- `ProductCard`, `VariantRow` in `@commerce/ui`
- api-client: catalog write methods + `Category` type

**Status:** implemented — `docs/catalog-merchant.md`.

## Phase 35 — Merchant addons UI

- Merchant PWA: `/catalog/addons` + product-addon linking on product detail
- `AddonCard` in `@commerce/ui`
- api-client: `linkProductAddon`

**Status:** implemented — `docs/catalog-addons.md`.

## Phase 36 — Business settings UI

- Merchant PWA: `/settings`, business profile, locations CRUD + hours editor
- `LocationCard` in `@commerce/ui`
- api-client: `updateBusiness`, `getLocation`, `createLocation`, `updateLocation`

**Status:** implemented — `docs/business-settings-ui.md`.

---

## MVP status

**MVP complete** — all three golden flows (Food, Hyperlocal, Courier) run on shared engines with experience apps (16–19), ONDC adapter (20), and lifecycle notifications (21).

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
