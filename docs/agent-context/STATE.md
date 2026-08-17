# Engine state (keep ≤80 lines)

Update this file **in the same PR** as the feature. Replace lines; do not append a changelog.

## Now

| Field | Value |
|-------|--------|
| Checkout | Phase 28 — Playwright API-backed E2E |
| API version | `0.19.0` (`backend/app/core/config.py`) |
| Base branch for new work | `cursor/phase-28-playwright-api-dfc8` |
| Branch name template | `cursor/<short-name>-dfc8` |
| Ops | CORS for dev/test PWAs; API client JSON Content-Type |
| Tests | through `e2e/tests/*-api.spec.ts` (2) — **60 backend**, **2 Playwright API**, **12 smoke** |

## Next recommended task

Merge stacked PR chain to `main`, or extend API E2E (merchant/rider flows, checkout browser path).

## Commands

```bash
pnpm ci
pnpm test:e2e:api
curl -s localhost:8000/health
```

## Last change

- Phase 28: Playwright flows wired to live API (customer register + admin settings meta)
- CORS for localhost PWAs in dev/test; api-client sets JSON Content-Type on POST bodies

## Known constraints

- E2E API uses SQLite `create_all` (not Alembic) via `scripts/start-e2e-api.sh`
- Map tiles require network; tracking is poll-based
