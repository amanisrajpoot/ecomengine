# Engine state (keep ≤80 lines)

Update this file **in the same PR** as the feature. Replace lines; do not append a changelog.

## Now

| Field | Value |
|-------|--------|
| Checkout | Phase 22 — merchant UI polish |
| API version | `0.16.0` (`backend/app/core/config.py`) |
| Base branch for new work | `cursor/phase-22-merchant-ui-polish-dfc8` |
| Branch name template | `cursor/<short-name>-dfc8` |
| Merchant PWA UX | Partner light theme, bottom nav, KDS order queue |
| Tests | through `test_phase20_ondc.py` (2) — **55 total** |

## Next recommended task

Rider UI polish, or E2E golden tests in CI.

## Commands

```bash
cd backend && PYTHONPATH=. python3 -m pytest -q
pnpm typecheck
pnpm --filter @commerce/merchant-pwa dev   # port 3001
```

## Last change

- Phase 22: Merchant PWA partner UX (dashboard stats, order queue filters, KDS actions)

## Known constraints

- Maps / live GPS tracking not yet in UI
- Money: integer paise only
