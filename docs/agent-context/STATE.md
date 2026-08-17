# Engine state (keep ≤80 lines)

Update this file **in the same PR** as the feature. Replace lines; do not append a changelog.

## Now

| Field | Value |
|-------|--------|
| Checkout | Phase 10 — settlements |
| API version | `0.10.0` (`backend/app/core/config.py`) |
| Base branch for new work | `cursor/phase-10-settlements-dfc8` |
| Branch name template | `cursor/<short-name>-dfc8` |
| API | settlements from ledger, lifecycle transitions, order linkage |
| Tests | through `test_phase10_settlements.py` (3) — **40 total** |

## Next recommended task

**Phase 11 — Fulfillment.**

Open [PHASES.md](./PHASES.md) Phase 11 section only — do not scan repo.

## Commands

```bash
cd backend && PYTHONPATH=. python3 -m pytest -q
pnpm typecheck
alembic upgrade head   # Postgres / Docker deploy
```

Docker: `cp .env.example .env && docker compose up --build`

## Last change

- Phase 10: Settlement calculate from ledger, RECONCILED→APPROVED→PAID transitions

## Known constraints

- Fulfillment decoupling in Phase 11
- Money: integer paise only
- ONDC adapter only in Phase 20
