# Engine state (keep ≤80 lines)

Update this file **in the same PR** as the feature. Replace lines; do not append a changelog.

## Now

| Field | Value |
|-------|--------|
| Checkout | Phase 8 — payments |
| API version | `0.8.0` (`backend/app/core/config.py`) |
| Base branch for new work | `cursor/phase-8-payments-dfc8` |
| Branch name template | `cursor/<short-name>-dfc8` |
| API | payments COD + Razorpay stub, refunds, order confirm hook |
| Tests | through `test_phase8_payments.py` (4) — **34 total** |

## Next recommended task

**Phase 9 — Ledger.**

Open [PHASES.md](./PHASES.md) Phase 9 section only — do not scan repo.

## Commands

```bash
cd backend && PYTHONPATH=. python3 -m pytest -q
pnpm typecheck
alembic upgrade head   # Postgres / Docker deploy
```

Docker: `cp .env.example .env && docker compose up --build`

## Last change

- Phase 8: PaymentGateway, COD auto-capture, Razorpay stub, refunds, idempotency

## Known constraints

- Ledger entries in Phase 9
- Money: integer paise only
- ONDC adapter only in Phase 20
