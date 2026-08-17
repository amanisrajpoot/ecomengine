# Engine state (keep ≤80 lines)

Update this file **in the same PR** as the feature. Replace lines; do not append a changelog.

## Now

| Field | Value |
|-------|--------|
| Checkout | Phase 18 — rider PWA |
| API version | `0.15.0` (`backend/app/core/config.py`) |
| Base branch for new work | `cursor/phase-18-rider-pwa-dfc8` |
| Branch name template | `cursor/<short-name>-dfc8` |
| Rider PWA | jobs, POD stops, order transitions, partner onboarding |
| Tests | through `test_phase12_delivery.py` (4) — **53 total** |

## Next recommended task

**Phase 19 — Admin web** (`apps/admin-web`).

Open [PHASES.md](./PHASES.md) Phase 19 section only — do not scan repo.

## Commands

```bash
cd backend && PYTHONPATH=. python3 -m pytest -q
pnpm typecheck
pnpm --filter @commerce/rider-pwa dev   # port 3002
alembic upgrade head   # Postgres / Docker deploy
```

Docker: `cp .env.example .env && docker compose up --build`

## Last change

- Phase 18: Rider PWA + `GET /deliveries/me` for assigned jobs

## Known constraints

- Admin UI Phase 19
- Money: integer paise only
- ONDC adapter only in Phase 20
