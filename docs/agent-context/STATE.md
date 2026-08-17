# Engine state (keep ≤80 lines)

Update this file **in the same PR** as the feature. Replace lines; do not append a changelog.

## Now

| Field | Value |
|-------|--------|
| Checkout | Phase 7 — orders |
| API version | `0.7.0` (`backend/app/core/config.py`) |
| Base branch for new work | `cursor/phase-7-orders-dfc8` |
| Branch name template | `cursor/<short-name>-dfc8` |
| API | through orders + configurable state machines |
| Tests | through `test_phase7_orders.py` (4) — **30 total** |

## Next recommended task

**Phase 8 — Payments.**

Open [PHASES.md](./PHASES.md) Phase 8 section only — do not scan repo.

## Commands

```bash
cd backend && PYTHONPATH=. python3 -m pytest -q
pnpm typecheck
alembic upgrade head   # Postgres / Docker deploy
```

Docker: `cp .env.example .env && docker compose up --build`

## Last change

- Phase 7: universal Order, checkout from cart, state machine profiles, status events

## Known constraints

- Payments module hooks transitions in Phase 8
- Money: integer paise in pricing snapshots
- ONDC adapter only in Phase 20
