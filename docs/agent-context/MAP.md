# Path map — open these files; do not walk the tree

Status: **Phase 15**. `[empty]` = package `__init__.py` only.

## Backend — always-on (exists)

| Path | Role |
|------|------|
| `backend/app/main.py` | FastAPI app; routers under `/api/v1`; lifespan bootstrap |
| `backend/app/core/config.py` | Settings + `app_version` |
| `backend/app/core/db.py` | Engine / session / `Base` |
| `backend/app/core/base.py` | ORM mixins |
| `backend/app/core/errors.py` | `AppError` |
| `backend/app/core/security.py` | JWT + passwords + OTP |
| `backend/app/core/deps.py` | Auth, tenant header, RBAC |
| `backend/app/core/redis.py` | Redis |
| `backend/app/core/events.py` | Event bus |
| `backend/tests/conftest.py` | Async client + SQLite test DB |
| `backend/tests/test_health.py` | Health/meta smoke |
| `backend/tests/test_phase1_foundation.py` | Auth + tenants |
| `backend/tests/test_phase2_business_location.py` | Businesses + locations |
| `backend/tests/test_phase3_catalog.py` | Catalog CRUD |
| `backend/tests/test_phase4_inventory.py` | Inventory + movements |
| `backend/tests/test_phase5_cart_pricing.py` | Cart + pricing |
| `backend/tests/test_phase6_tax.py` | Tax rules + calculate |
| `backend/tests/test_phase7_orders.py` | Checkout + FSM |
| `backend/tests/test_phase8_payments.py` | COD, capture, refunds |
| `backend/tests/test_phase9_ledger.py` | Ledger capture + refund |
| `backend/tests/test_phase10_settlements.py` | Settlement calculate + lifecycle |
| `backend/tests/test_phase11_fulfillment.py` | Fulfillment checkout + lifecycle |
| `backend/tests/test_phase12_delivery.py` | Partners, assign, stops |
| `backend/tests/test_phase13_food_golden.py` | Food e2e golden path |
| `backend/tests/test_phase14_hyperlocal.py` | Hyperlocal inventory path |
| `backend/tests/test_phase15_courier.py` | Courier quote + golden path |
| `backend/tests/test_phase20_ondc.py` | ONDC search → confirm → status |
| `backend/alembic/` | Migrations through `phase12_delivery` |

## Backend modules — expected files (do not Glob)

Canonical per module: `models.py`, `schemas.py`, `service.py`, `router.py`. Optional: `handlers.py` (events), `rbac.py` (identity), `states.py` (orders).

| Module | Now | Spec | Schema offset (see SCHEMA.md) | Include router in |
|--------|-----|------|-------------------------------|-------------------|
| `identity` | models, schemas, service, router, rbac | permissions.md | identity ~39 | `main.py` |
| `tenants` | models, schemas, service, router (+ platform_router) | api-conventions Tenancy | tenancy ~15 | `main.py` |
| `businesses` | models, schemas, service, router | domain-model Business | businesses ~106 | `main.py` |
| `locations` | models, schemas, service, router | domain-model Location | business_locations ~126 | nested under businesses |
| `catalog` | models, schemas, service, router | domain-model Catalog | catalog ~144 | `main.py` |
| `inventory` | models, schemas, service, router, order_hooks | domain-model Inventory | inventory ~225 | `main.py` |
| `cart` | models, schemas, service, router | domain-model Cart | carts ~264 | `main.py` |
| `pricing` | schemas, service, courier, router | pricing-engine.md | — | `main.py` |
| `taxation` | models, schemas, service, router | tax-engine.md | tax ~371 | `main.py` |
| `orders` | models, schemas, service, router, states | order-state-machines.md | orders ~290 | `main.py` |
| `payments` | models, schemas, service, router, gateway | domain-model Payments | payments ~336 | `main.py` |
| `ledger` | models, schemas, service, router | settlement-engine LedgerEntry | ledger ~394 | `main.py` |
| `settlements` | models, schemas, service, router, states | settlement-engine.md | settlements ~412 | `main.py` |
| `fulfillment` | models, schemas, service, router, states | fulfillment.md | fulfillments ~438 | `main.py` |
| `delivery` | models, schemas, service, router, states | fulfillment.md Delivery | deliveries ~451 | `main.py` |
| `partners` | models, schemas, service, router | fulfillment.md Partner | partner ~78 | `main.py` |
| `promotions` | empty | schema promotions | promotions ~481 | later |
| `notifications` | empty | architecture events | — | later |
| `support` | empty | — | — | later |
| `reviews` | empty | — | — | later |
| `integrations` | `ondc/` router, schemas, service, mapper | architecture adapters | — | `main.py` includes `ondc_router` only |

## Packages (exists)

| Path | Role | Touch when |
|------|------|------------|
| `packages/types/src/index.ts` | User, Tenant, Business, catalog types | Any new API resource |
| `packages/api-client/src/index.ts` | auth through delivery + `assignUserRole` | Merchant admin |
| `packages/ui/src/index.ts` | Button, Card, Input, PriceDisplay, Badge, SearchBar, BusinessCard, ProductCard, CategoryChip, OrderTimeline, Skeleton, EmptyState | New shared component |
| `packages/config/` | tsconfig | Tooling only |

## Apps — on disk now

Do not search other `app/` folders unless sharing components:

| App | Layout | Routes (customer-pwa) | Config |
|-----|--------|-------------------------|--------|
| `apps/customer-pwa` | `app/layout.tsx`, `components/AppShell.tsx`, `components/CartPeek.tsx` | `/`, `/login`, `/register`, `/settings`, `/businesses`, `/business/[businessId]`, `/cart`, `/checkout`, `/orders`, `/orders/[orderId]`, `/courier` | consumer UX: bottom nav, search, cards |
| `apps/merchant-pwa` | `app/layout.tsx`, `components/AppShell.tsx` | `/`, `/login`, `/register`, `/settings`, `/businesses`, `/business/[businessId]`, `/business/[businessId]/orders`, `/business/[businessId]/orders/[orderId]`, `/business/[businessId]/catalog`, `/business/[businessId]/catalog/new`, `/business/[businessId]/catalog/[productId]` | `lib/api.ts`, `lib/session.ts`, `lib/orderTransitions.ts` |
| `apps/rider-pwa` | `app/layout.tsx`, `components/AppShell.tsx` | `/`, `/login`, `/register`, `/settings`, `/onboarding`, `/jobs`, `/jobs/[deliveryId]` | `lib/api.ts`, `lib/session.ts`, `lib/orderTransitions.ts` |
| `apps/admin-web` | `app/layout.tsx`, `components/AppShell.tsx` | `/`, `/login`, `/settings`, `/tenants`, `/orders`, `/orders/[orderId]`, `/settlements`, `/users/roles` | `lib/api.ts`, `lib/session.ts` |

New screens go next to those `app/` trees. Register the route in this table when added.

## Repo root

| Path | Role |
|------|------|
| `docker-compose.yml` | API, Postgres, Redis, MinIO |
| `.env.example` | Local env |
| `package.json` | pnpm scripts: `typecheck`, `dev:*` |
| `pnpm-workspace.yaml` | workspaces |
| `docs/*.md` | Specs — use INDEX/SCHEMA offsets, do not read all |
| `docs/agent-context/` | This pack |
| `AGENTS.md` | Pointer |
| `.cursor/rules/agent-context.mdc` | Always-on load rule |

## After adding files

Update **this MAP** (tick empty → list new filenames) and one INDEX/ROUTES/PHASES row. That is how the index stays self-aware without scanning.
