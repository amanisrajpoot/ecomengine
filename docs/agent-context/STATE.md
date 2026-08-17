# Engine state (keep ≤80 lines)

Update this file **in the same PR** as the feature. Replace lines; do not append a changelog.

## Now

| Field | Value |
|-------|--------|
| Checkout | Phase 21 — customer UI polish |
| API version | `0.16.0` (`backend/app/core/config.py`) |
| Base branch for new work | `cursor/phase-21-customer-ui-polish-dfc8` |
| Branch name template | `cursor/<short-name>-dfc8` |
| Customer PWA UX | Swiggy-style home, cards, bottom nav, cart peek, tracking |
| Tests | through `test_phase20_ondc.py` (2) — **55 total** |

## Next recommended task

Merchant / rider UI polish, or E2E golden tests in CI.

## Commands

```bash
cd backend && PYTHONPATH=. python3 -m pytest -q
pnpm typecheck
pnpm --filter @commerce/customer-pwa dev   # port 3000
```

## Last change

- Phase 21: Customer PWA consumer UX (search, categories, product cards, order timeline)

## Known constraints

- Maps / live GPS tracking not yet in UI
- Money: integer paise only
