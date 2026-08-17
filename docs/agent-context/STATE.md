# Engine state (keep ≤80 lines)

Update this file **in the same PR** as the feature. Replace lines; do not append a changelog.

## Now

| Field | Value |
|-------|--------|
| Checkout | Phase 27 — production hardening |
| API version | `0.18.0` (`backend/app/core/config.py`) |
| Base branch for new work | `cursor/phase-27-prod-hardening-dfc8` |
| Branch name template | `cursor/<short-name>-dfc8` |
| Ops | Rate limits (429), `/metrics`, request ID + timing headers |
| Tests | through `test_phase27_prod_hardening.py` (4) — **60 total**, **3 golden** |

## Next recommended task

Merge stacked PR chain to `main`, or add Playwright flows wired to live API.

## Commands

```bash
pnpm ci
curl -s localhost:8000/health
curl -s localhost:8000/metrics
```

## Last change

- Phase 27: Rate limiting, Prometheus metrics, observability middleware

## Known constraints

- Rate limit uses Redis when available; in-memory fallback otherwise
- Map tiles require network; tracking is poll-based
