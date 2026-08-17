# Engine state (keep ≤80 lines)

Update this file **in the same PR** as the feature. Replace lines; do not append a changelog.

## Now

| Field | Value |
|-------|--------|
| Checkout | Phase 0 — specs + monorepo scaffold |
| API version | `0.0.0` (`backend/app/core/config.py`) |
| Base branch for new work | `cursor/phase-0-scaffold-dfc8` |
| Branch name template | `cursor/<short-name>-dfc8` |
| Apps | Shell-only Next.js PWAs (customer, merchant, rider, admin) |
| API | FastAPI `/health` + `/api/v1/meta` only |
| Tests | `backend/tests/test_health.py` |

## Next recommended task

**Phase 1 — Platform foundation** (auth, identity, RBAC, tenancy, config).

Read after INDEX + this file:

1. `docs/milestones.md` (Phase 1 section only)
2. `docs/permissions.md`
3. `docs/api-conventions.md`
4. `docs/schema.md` (tenants, users, role bindings — skip later tables)
5. `backend/app/main.py`, `backend/app/core/`
6. `backend/app/identity/`, `backend/app/tenants/` (packages exist, empty)

## Commands

```bash
# API
cd backend && PYTHONPATH=. pytest -q

# Frontends
pnpm typecheck
```

Docker: `cp .env.example .env && docker compose up --build`

## Last change

- Agent-context pack: `docs/agent-context/`, `AGENTS.md`, `.cursor/rules/agent-context.mdc`

## Known constraints

- No domain routers yet — do not invent `FoodOrder` tables when Phase 1–7 land
- Money: integer paise when pricing exists
- ONDC stays an adapter (Phase 20)
