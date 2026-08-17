# Engine state (keep ≤80 lines)

Update this file **in the same PR** as the feature. Replace lines; do not append a changelog.

## Now

| Field | Value |
|-------|--------|
| Checkout | Phase 12 — delivery |
| API version | `0.12.0` (`backend/app/core/config.py`) |
| Base branch for new work | `cursor/phase-12-delivery-dfc8` |
| Branch name template | `cursor/<short-name>-dfc8` |
| API | partners, vehicles, deliveries, stops, assignment V1 |
| Tests | through `test_phase12_delivery.py` (3) — **46 total** |

## Next recommended task

**Phase 13 — Food golden path.**

Open [PHASES.md](./PHASES.md) Phase 13 section only — do not scan repo.

## Commands

```bash
cd backend && PYTHONPATH=. python3 -m pytest -q
pnpm typecheck
alembic upgrade head   # Postgres / Docker deploy
```

Docker: `cp .env.example .env && docker compose up --build`

## Last change

- Phase 12: Delivery partners, nearest-rider assign, stop completion + POD

## Known constraints

- Food golden path tests in Phase 13
- Money: integer paise only
- ONDC adapter only in Phase 20
