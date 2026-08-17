# Engine state (keep ≤80 lines)

Update this file **in the same PR** as the feature. Replace lines; do not append a changelog.

## Now

| Field | Value |
|-------|--------|
| Checkout | **Merged to `main`** — phases 0–28 (backend + four PWAs + E2E) |
| API version | `0.19.0` (`backend/app/core/config.py`) |
| Base branch for new work | `main` |
| Branch name template | `cursor/<short-name>-dfc8` |
| Ops | CORS (dev/test), rate limits, `/metrics`, Playwright smoke + API E2E |
| Tests | **60** backend pytest, **3** golden, **12** smoke E2E, **2** API E2E |

## Next recommended task

Open a new branch from `main` for the alternate UI stack (phases 22–39 demo/dispatch/UI PRs) or next product slice.

## Commands

```bash
pnpm ci
pnpm test:e2e:api
curl -s localhost:8000/health
```

## Last change

- Stacked phase chain (0–28) fast-forward merged into `main`

## Known constraints

- E2E API uses SQLite `create_all` (not Alembic) via `scripts/start-e2e-api.sh`
- Open PRs #2–53 may still show open on GitHub; code is on `main` — close manually if desired
