# Engine state (keep ≤80 lines)

Update this file **in the same PR** as the feature. Replace lines; do not append a changelog.

## Now

| Field | Value |
|-------|--------|
| Checkout | Phase 4 — inventory |
| API version | `0.4.0` (`backend/app/core/config.py`) |
| Base branch for new work | `cursor/phase-4-inventory-dfc8` |
| Branch name template | `cursor/<short-name>-dfc8` |
| API | Auth, tenants, RBAC, businesses, locations, catalog, inventory |
| Tests | through `test_phase4_inventory.py` (4) — **19 total** with prior phases |

## Next recommended task

**Phase 5 — Cart + pricing.**

Open [PHASES.md](./PHASES.md) Phase 5 section only — do not scan repo.

## Commands

```bash
cd backend && PYTHONPATH=. python3 -m pytest -q
pnpm typecheck
alembic upgrade head   # Postgres / Docker deploy
```

Docker: `cp .env.example .env && docker compose up --build`

## Last change

- Phase 4: inventory items, stock movements, reserve/release, low-stock

## Known constraints

- One `Order` model when Phase 7 lands
- Money: integer paise when pricing exists
- ONDC adapter only in Phase 20
