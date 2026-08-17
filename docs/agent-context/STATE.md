# Engine state (keep ≤80 lines)

Update this file **in the same PR** as the feature. Replace lines; do not append a changelog.

## Now

| Field | Value |
|-------|--------|
| Checkout | Phase 23 — rider UI polish |
| API version | `0.16.0` (`backend/app/core/config.py`) |
| Base branch for new work | `cursor/phase-23-rider-ui-polish-dfc8` |
| Branch name template | `cursor/<short-name>-dfc8` |
| Rider PWA UX | Blue delivery theme, bottom nav, job cards, stop POD flow |
| Tests | through `test_phase20_ondc.py` (2) — **55 total** |

## Next recommended task

E2E golden tests in CI, or maps/GPS live tracking UI.

## Commands

```bash
cd backend && PYTHONPATH=. python3 -m pytest -q
pnpm typecheck
pnpm --filter @commerce/rider-pwa dev   # port 3002
```

## Last change

- Phase 23: Rider PWA delivery UX (job queue cards, route timeline, go online/offline)

## Known constraints

- Maps / live GPS tracking not yet in UI
- Money: integer paise only
