# Engine state (keep ≤80 lines)

Update this file **in the same PR** as the feature. Replace lines; do not append a changelog.

## Now

| Field | Value |
|-------|--------|
| Checkout | Phase 16 — customer PWA |
| API version | `0.15.0` (`backend/app/core/config.py`) |
| Base branch for new work | `cursor/phase-16-customer-pwa-dfc8` |
| Branch name template | `cursor/<short-name>-dfc8` |
| Customer PWA | browse, catalog, cart, checkout, orders, courier quote |
| Tests | through `test_phase15_courier.py` (2) — **52 total** |

## Next recommended task

**Phase 17 — Merchant PWA** (`apps/merchant-pwa`).

Open [PHASES.md](./PHASES.md) Phase 17 section only — do not scan repo.

## Commands

```bash
cd backend && PYTHONPATH=. python3 -m pytest -q
pnpm typecheck
pnpm --filter @commerce/customer-pwa dev   # port 3000
alembic upgrade head   # Postgres / Docker deploy
```

Docker: `cp .env.example .env && docker compose up --build`

## Last change

- Phase 16: Customer PWA wired to api-client (auth, catalog, cart, COD checkout, orders, courier)

## Known constraints

- Merchant / rider / admin UIs Phases 17–19
- Money: integer paise only
- ONDC adapter only in Phase 20
