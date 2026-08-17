# Engine state (keep ≤80 lines)

Update this file **in the same PR** as the feature. Replace lines; do not append a changelog.

## Now

| Field | Value |
|-------|--------|
| Checkout | Phase 24 — maps / GPS live tracking |
| API version | `0.17.0` (`backend/app/core/config.py`) |
| Base branch for new work | `cursor/phase-24-maps-gps-tracking-dfc8` |
| Branch name template | `cursor/<short-name>-dfc8` |
| Live tracking | `GET /orders/{id}/tracking`, `LiveMap`, rider GPS ping |
| Tests | through `test_phase24_tracking.py` (1) — **56 total** |

## Next recommended task

E2E golden tests in CI.

## Commands

```bash
cd backend && PYTHONPATH=. python3 -m pytest -q
pnpm typecheck
pnpm --filter @commerce/customer-pwa dev   # port 3000
pnpm --filter @commerce/rider-pwa dev      # port 3002
```

## Last change

- Phase 24: Order tracking API, Leaflet map UI, rider live GPS uploads

## Known constraints

- Map tiles require network (OpenStreetMap); no WebSocket stream yet (poll-based)
- Money: integer paise only
