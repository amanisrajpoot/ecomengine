# Engine state (keep ≤80 lines)

Update this file **in the same PR** as the feature. Replace lines; do not append a changelog.

## Now

| Field | Value |
|-------|--------|
| Checkout | Phase 13 — Food golden path |
| API version | `0.12.0` (`backend/app/core/config.py`) |
| Base branch for new work | `cursor/phase-13-food-golden-dfc8` |
| Branch name template | `cursor/<short-name>-dfc8` |
| API | unchanged — integration tests only |
| Tests | through `test_phase13_food_golden.py` (2) — **48 total** |

## Next recommended task

**Phase 14 — Hyperlocal.**

Open [PHASES.md](./PHASES.md) Phase 14 section only — do not scan repo.

## Commands

```bash
cd backend && PYTHONPATH=. python3 -m pytest -q
pnpm typecheck
alembic upgrade head   # Postgres / Docker deploy
```

Docker: `cp .env.example .env && docker compose up --build`

## Last change

- Phase 13: Food golden path e2e test through settlement (no new tables)

## Known constraints

- Hyperlocal inventory path in Phase 14
- Money: integer paise only
- ONDC adapter only in Phase 20
