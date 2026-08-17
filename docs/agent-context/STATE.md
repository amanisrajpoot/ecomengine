# Engine state (keep ≤80 lines)

Update this file **in the same PR** as the feature. Replace lines; do not append a changelog.

## Now

| Field | Value |
|-------|--------|
| Checkout | Phase 15 — courier |
| API version | `0.15.0` (`backend/app/core/config.py`) |
| Base branch for new work | `cursor/phase-15-courier-dfc8` |
| Branch name template | `cursor/<short-name>-dfc8` |
| API | courier quote, MULTI_STOP cart lines, golden path tests |
| Tests | through `test_phase15_courier.py` (2) — **52 total** |

## Next recommended task

**Phase 16 — Customer PWA** (`apps/customer-pwa`).

Open [PHASES.md](./PHASES.md) Phase 16 section only — do not scan repo.

## Commands

```bash
cd backend && PYTHONPATH=. python3 -m pytest -q
pnpm typecheck
alembic upgrade head   # Postgres / Docker deploy
```

Docker: `cp .env.example .env && docker compose up --build`

## Last change

- Phase 15: Courier fare quote + golden path through POD and settlement

## Known constraints

- Experience apps Phases 16–19
- Money: integer paise only
- ONDC adapter only in Phase 20
