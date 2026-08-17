# Engine state (keep ≤80 lines)

Update this file **in the same PR** as the feature. Replace lines; do not append a changelog.

## Now

| Field | Value |
|-------|--------|
| Checkout | Phase 5 — cart + pricing |
| API version | `0.5.0` (`backend/app/core/config.py`) |
| Base branch for new work | `cursor/phase-5-cart-pricing-dfc8` |
| Branch name template | `cursor/<short-name>-dfc8` |
| API | through cart + pricing breakdown |
| Tests | through `test_phase5_cart_pricing.py` (3) — **22 total** |

## Next recommended task

**Phase 6 — Tax.**

Open [PHASES.md](./PHASES.md) Phase 6 section only — do not scan repo.

## Commands

```bash
cd backend && PYTHONPATH=. python3 -m pytest -q
pnpm typecheck
alembic upgrade head   # Postgres / Docker deploy
```

Docker: `cp .env.example .env && docker compose up --build`

## Last change

- Phase 5: cart aggregate, pricing pipeline, breakdown snapshot on cart

## Known constraints

- One `Order` model when Phase 7 lands
- Money: integer paise when pricing exists
- Tax stub in pricing until Phase 6 taxation module
- ONDC adapter only in Phase 20
