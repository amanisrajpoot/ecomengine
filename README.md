# Commerce Engine

Universal Commerce & Fulfillment Engine — modular monolith monorepo (India-first V1).

## What's in this repo

| Path | Description |
|------|-------------|
| `docs/` | Phase 0 domain & architecture specifications |
| `backend/` | FastAPI modular monolith |
| `apps/` | Customer / Merchant / Rider PWAs + Admin web |
| `packages/` | Shared TypeScript types, API client, UI, config |

## Current status

- **Phase 0** — specs + scaffold
- **Phase 1** — auth (OTP + password), identity/RBAC, multi-tenancy, platform/tenant/business config
- **Phase 2** — business onboarding, capability presets, locations (address/geo/hours)
- **Phase 3** — catalog (categories, products, variants, addons, bundles)
- **Phase 4** — inventory (optional; receive/reserve/release/consume + movements)
- **Phase 5** — cart + pricing pipeline (breakdown snapshots; tax stub)
- **Phase 6** — tax engine (`TaxRule`; customer vs platform vs settlement kinds)
- **Phase 7** — orders (checkout + configurable state machines)
- **Phase 8** — payments (multi-gateway: Cashfree + COD; mock mode for local/dev)
- **Phase 9** — ledger (immutable balanced postings from payment events)
- **Phase 10** — settlements (ledger → merchant/rider/platform payout lifecycle)
- **Phase 11** — fulfillment (1:1 with order; delivery/partners in Phase 12)
- **Phase 12** — delivery (partners, vehicles, nearest assignment, tracking, POD)
- **Phase 13** — Food vertical golden path + order debugger (shared engines)
- **Phase 14** — Hyperlocal (store discovery + inventory reserve/consume on order lifecycle)
- **Phase 15** — Courier (quote by distance/weight/vehicle + pickup/drop on shared engines)
- **Phase 16** — Customer PWA (browse, cart checkout, courier book, orders)
- **Phase 17** — Merchant PWA (order queue + kitchen transitions)
- **Phase 18** — Rider PWA (assignments, POD, go-online)
- **Phase 19** — Admin web (tenant list, order debugger, ops dashboard on port 3003)
- **Phase 20** — ONDC adapter (Beckn BPP: search → confirm on shared engines)
- **Phase 21** — Notifications (order lifecycle SMS fan-out, mock channel)
- **Phase 22** — Unified demo seed + local testing guide (`docs/demo.md`)

## Test with demo data

**You can test all apps now.** See **[docs/demo.md](docs/demo.md)** for the full walkthrough.

```bash
docker compose up --build          # API + demo seed on first boot
pnpm demo:seed && source demo.env  # or re-seed locally
pnpm dev:customer                  # :3000 — customer@demo.com / Demo123!
pnpm dev:merchant                  # :3001 — merchant@demo.com / Demo123!
pnpm dev:rider                     # :3002 — rider@demo.com / Demo123!
pnpm dev:admin                     # :3003 — admin@example.com / ChangeMe123!
```

Paste `NEXT_PUBLIC_TENANT_ID` from `demo.env` into each app login screen (or set via `.env.local`).

## Prerequisites

- Docker & Docker Compose (recommended), or local PostgreSQL 16+
- Node.js 22+ and pnpm
- Python 3.12+

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

- API health: http://localhost:8000/health
- API docs: http://localhost:8000/docs
- MinIO console: http://localhost:9001 (minioadmin / minioadmin)

## Deploy full stack (Docker)

Run API + all four PWAs on any VPS (Oracle, DigitalOcean, etc.):

```bash
cp .env.production.example .env   # edit PUBLIC_HOST, secrets, CORS
pnpm deploy:up                    # or: docker compose -f docker-compose.prod.yml up -d --build
```

See **[docs/deploy.md](docs/deploy.md)** for Oracle Free Tier steps and demo credentials.

### Backend (local without Docker for the API)

```bash
# Ensure Postgres is reachable at DATABASE_URL
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. alembic upgrade head
PYTHONPATH=. python -m app.scripts.bootstrap_super_admin
PYTHONPATH=. python -m app.scripts.seed_tax_rules
# Optional unified demo (all verticals + PWA users in one tenant):
PYTHONPATH=. python -m app.scripts.seed_demo
# Writes ../demo.env — source it before starting PWAs
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
PYTHONPATH=. pytest
```

Default bootstrap admin: `admin@example.com` / `ChangeMe123!` (override via env).

### Phase 1 auth notes

- Send `X-Tenant-ID: <uuid>` for tenant-scoped auth/register/login.
- In development, `POST /api/v1/auth/otp/request` returns `debug_code`.
- Use `Authorization: Bearer <access_token>` for protected routes.

### Frontend apps

```bash
pnpm install
pnpm --filter @commerce/customer-pwa dev
# or merchant-pwa | rider-pwa | admin-web
```

## Documentation

Start at [docs/README.md](docs/README.md).

## License

Proprietary — all rights reserved.
