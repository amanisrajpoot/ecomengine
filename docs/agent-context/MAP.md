# Path map — open these files; do not walk the tree

Status: **Phase 0**. `[empty]` = package `__init__.py` only. When you add `models.py` / `router.py`, tick this table in the same PR.

## Backend — always-on (exists)

| Path | Role |
|------|------|
| `backend/app/main.py` | FastAPI app; `/health`, `/api/v1/meta` — **include new routers here** |
| `backend/app/core/config.py` | Settings + `app_version` |
| `backend/app/core/db.py` | Engine / session |
| `backend/app/core/redis.py` | Redis |
| `backend/app/core/events.py` | In-process event bus |
| `backend/tests/test_health.py` | Health test |
| `backend/requirements.txt` | Python deps |
| `backend/Dockerfile` | API image |
| `backend/alembic/` | **Create at Phase 1** with first migration |

## Backend modules — expected files (do not Glob)

Canonical per module: `models.py`, `schemas.py`, `service.py`, `router.py`. Optional: `handlers.py` (events), `rbac.py` (identity), `states.py` (orders).

| Module | Now | Spec | Schema offset (see SCHEMA.md) | Include router in |
|--------|-----|------|-------------------------------|-------------------|
| `identity` | empty | permissions.md | identity ~39 | `main.py` |
| `tenants` | empty | api-conventions Tenancy | tenancy ~15 | `main.py` |
| `businesses` | empty | domain-model Business | businesses ~106 | `main.py` |
| `locations` | empty | domain-model Location | business_locations ~126 | usually mounted under businesses |
| `catalog` | empty | domain-model Catalog | catalog ~144 | `main.py` |
| `inventory` | empty | domain-model Inventory | inventory ~225 | `main.py` |
| `cart` | empty | domain-model Cart | carts ~264 | `main.py` |
| `pricing` | empty | pricing-engine.md | — | called from cart/orders, maybe no public router |
| `taxation` | empty | tax-engine.md | tax ~371 | admin rules + calculate |
| `orders` | empty | order-state-machines.md | orders ~290 | `main.py` |
| `payments` | empty | domain-model Payments | payments ~336 | `main.py` |
| `ledger` | empty | settlement-engine LedgerEntry | ledger ~394 | `main.py` |
| `settlements` | empty | settlement-engine.md | settlements ~412 | `main.py` |
| `fulfillment` | empty | fulfillment.md | fulfillments ~438 | `main.py` |
| `delivery` | empty | fulfillment.md Delivery | deliveries ~451 | `main.py` |
| `partners` | empty | fulfillment.md Partner | delivery_partner_profiles ~78 | `main.py` |
| `promotions` | empty | schema promotions | promotions ~481 | later |
| `notifications` | empty | architecture events | — | later |
| `support` | empty | — | — | later |
| `reviews` | empty | — | — | later |
| `integrations` | empty | architecture adapters | — | Phase 20 `integrations/ondc/` |

## Packages (exists)

| Path | Role | Touch when |
|------|------|------------|
| `packages/types/src/index.ts` | Shared TS types | Any new API resource |
| `packages/api-client/src/index.ts` | `createApiClient` — only `getHealth`/`getMeta` now | Any new HTTP method |
| `packages/ui/src/index.ts` | UI barrel | New shared component |
| `packages/config/` | tsconfig | Tooling only |

## Apps — on disk now (shells only)

Do not search other `app/` folders; these are the pages:

| App | Layout | Home | Config |
|-----|--------|------|--------|
| `apps/customer-pwa` | `app/layout.tsx` | `app/page.tsx` | `package.json`, `next.config.ts`, `tailwind.config.ts` |
| `apps/merchant-pwa` | same | same | same |
| `apps/rider-pwa` | same | same | same |
| `apps/admin-web` | same | same | same |

New screens go next to those `app/` trees (e.g. `apps/customer-pwa/app/orders/page.tsx`). Register the route in this table when added.

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
