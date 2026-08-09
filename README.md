# Commerce Engine

Universal Commerce & Fulfillment Engine — modular monolith monorepo (India-first V1).

## What's in this repo

| Path | Description |
|------|-------------|
| `docs/` | Phase 0 domain & architecture specifications |
| `backend/` | FastAPI modular monolith |
| `apps/` | Customer / Merchant / Rider PWAs + Admin web |
| `packages/` | Shared TypeScript types, API client, UI, config |

Phase 0 delivers **specs + scaffold only** (no business logic yet).

## Prerequisites

- Docker & Docker Compose
- Node.js 22+ and pnpm
- Python 3.12+ (for local backend tests without Docker)

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

- API health: http://localhost:8000/health
- API meta: http://localhost:8000/api/v1/meta
- MinIO console: http://localhost:9001 (minioadmin / minioadmin)

### Backend tests (local)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

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
