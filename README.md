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

### Backend (local without Docker for the API)

```bash
# Ensure Postgres is reachable at DATABASE_URL
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. alembic upgrade head
PYTHONPATH=. python -m app.scripts.bootstrap_super_admin
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
