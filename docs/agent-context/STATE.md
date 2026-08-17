# Engine state (keep ≤80 lines)

Update this file **in the same PR** as the feature. Replace lines; do not append a changelog.

## Now

| Field | Value |
|-------|--------|
| Checkout | Phase 11 — fulfillment |
| API version | `0.11.0` (`backend/app/core/config.py`) |
| Base branch for new work | `cursor/phase-11-fulfillment-dfc8` |
| Branch name template | `cursor/<short-name>-dfc8` |
| API | fulfillments decoupled from orders, checkout hook, lifecycle |
| Tests | through `test_phase11_fulfillment.py` (3) — **43 total** |

## Next recommended task

**Phase 12 — Delivery.**

Open [PHASES.md](./PHASES.md) Phase 12 section only — do not scan repo.

## Commands

```bash
cd backend && PYTHONPATH=. python3 -m pytest -q
pnpm typecheck
alembic upgrade head   # Postgres / Docker deploy
```

Docker: `cp .env.example .env && docker compose up --build`

## Last change

- Phase 11: Fulfillment entity per order, types, PENDING→ACTIVE→COMPLETED

## Known constraints

- Delivery module in Phase 12
- Money: integer paise only
- ONDC adapter only in Phase 20
