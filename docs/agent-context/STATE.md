# Engine state (keep ≤80 lines)

Update this file **in the same PR** as the feature. Replace lines; do not append a changelog.

## Now

| Field | Value |
|-------|--------|
| Checkout | Phase 3 — catalog |
| API version | `0.3.0` (`backend/app/core/config.py`) |
| Base branch for new work | `cursor/phase-3-catalog-dfc8` |
| Branch name template | `cursor/<short-name>-dfc8` |
| API | Auth, tenants, RBAC, businesses, locations, catalog |
| Tests | `test_health.py`, `test_phase1_foundation.py` (7), `test_phase2_business_location.py` (4), `test_phase3_catalog.py` (4) |

## Next recommended task

**Phase 4 — Inventory.**

Open [PHASES.md](./PHASES.md) Phase 4 section only — do not scan repo.

## Commands

```bash
cd backend && PYTHONPATH=. python3 -m pytest -q
pnpm typecheck
alembic upgrade head   # Postgres / Docker deploy
```

Docker: `cp .env.example .env && docker compose up --build`

## Last change

- Phase 3: categories, products, variants, addons, bundles, capability gates

## Known constraints

- One `Order` model when Phase 7 lands
- Money: integer paise when pricing exists
- ONDC adapter only in Phase 20
