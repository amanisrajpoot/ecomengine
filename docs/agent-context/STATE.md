# Engine state (keep ≤80 lines)

Update this file **in the same PR** as the feature. Replace lines; do not append a changelog.

## Now

| Field | Value |
|-------|--------|
| Checkout | Phase 2 — business & location |
| API version | `0.2.0` (`backend/app/core/config.py`) |
| Base branch for new work | `cursor/phase-2-business-location-dfc8` |
| Branch name template | `cursor/<short-name>-dfc8` |
| API | Auth, tenants, RBAC, businesses, locations |
| Tests | `test_health.py`, `test_phase1_foundation.py` (7), `test_phase2_business_location.py` (4) |

## Next recommended task

**Phase 3 — Catalog.**

Open [PHASES.md](./PHASES.md) Phase 3 section only — do not scan repo.

## Commands

```bash
cd backend && PYTHONPATH=. python3 -m pytest -q
pnpm typecheck
alembic upgrade head   # Postgres / Docker deploy
```

Docker: `cp .env.example .env && docker compose up --build`

## Last change

- Phase 2: businesses CRUD, capability presets by type, nested locations, alembic `phase2_business_location`

## Known constraints

- One `Order` model when Phase 7 lands
- Money: integer paise when pricing exists
- ONDC adapter only in Phase 20
