# Engine state (keep ≤80 lines)

Update this file **in the same PR** as the feature. Replace lines; do not append a changelog.

## Now

| Field | Value |
|-------|--------|
| Checkout | Phase 1 — platform foundation |
| API version | `0.1.0` (`backend/app/core/config.py`) |
| Base branch for new work | `cursor/phase-1-foundation-dfc8` |
| Branch name template | `cursor/<short-name>-dfc8` |
| API | Auth, tenants, RBAC, bootstrap super admin |
| Tests | `backend/tests/test_health.py`, `test_phase1_foundation.py` (7) |

## Next recommended task

**Phase 2 — Business & location.**

Open [PHASES.md](./PHASES.md) Phase 2 section only — do not scan repo.

## Commands

```bash
cd backend && PYTHONPATH=. python3 -m pytest -q
pnpm typecheck
alembic upgrade head   # Postgres / Docker deploy
```

Docker: `cp .env.example .env && docker compose up --build`

## Last change

- Phase 1: identity, tenants, alembic, JWT auth, OTP, RBAC deps

## Known constraints

- One `Order` model when Phase 7 lands
- Money: integer paise when pricing exists
- ONDC adapter only in Phase 20
