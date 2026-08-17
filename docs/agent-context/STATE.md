# Engine state (keep ≤80 lines)

Update this file **in the same PR** as the feature. Replace lines; do not append a changelog.

## Now

| Field | Value |
|-------|--------|
| Checkout | Phase 9 — ledger |
| API version | `0.9.0` (`backend/app/core/config.py`) |
| Base branch for new work | `cursor/phase-9-ledger-dfc8` |
| Branch name template | `cursor/<short-name>-dfc8` |
| API | immutable ledger on payment capture + refund reversal |
| Tests | through `test_phase9_ledger.py` (3) — **37 total** |

## Next recommended task

**Phase 10 — Settlements.**

Open [PHASES.md](./PHASES.md) Phase 10 section only — do not scan repo.

## Commands

```bash
cd backend && PYTHONPATH=. python3 -m pytest -q
pnpm typecheck
alembic upgrade head   # Postgres / Docker deploy
```

Docker: `cp .env.example .env && docker compose up --build`

## Last change

- Phase 9: Ledger entries on PAYMENT_CAPTURED / REFUND_COMPLETED, balanced postings

## Known constraints

- Settlements aggregate ledger in Phase 10
- Money: integer paise only
- ONDC adapter only in Phase 20
