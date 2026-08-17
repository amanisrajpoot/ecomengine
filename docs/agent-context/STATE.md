# Engine state (keep ≤80 lines)

Update this file **in the same PR** as the feature. Replace lines; do not append a changelog.

## Now

| Field | Value |
|-------|--------|
| Checkout | Phase 20 — ONDC adapter |
| API version | `0.16.0` (`backend/app/core/config.py`) |
| Base branch for new work | `cursor/phase-20-ondc-adapter-dfc8` |
| Branch name template | `cursor/<short-name>-dfc8` |
| ONDC | Beckn-style search/select/init/confirm/status under `/api/v1/ondc` |
| Tests | through `test_phase20_ondc.py` (2) — **55 total** |

## Next recommended task

MVP complete (Phases 0–20). Hardening: UI polish, E2E golden tests in CI, production deploy.

## Commands

```bash
cd backend && PYTHONPATH=. python3 -m pytest -q
pnpm typecheck
alembic upgrade head   # Postgres / Docker deploy
```

Docker: `cp .env.example .env && docker compose up --build`

## Last change

- Phase 20: ONDC adapter in `integrations/ondc/` (core does not import ONDC)

## Known constraints

- Money: integer paise only
- ONDC only via adapter layer
