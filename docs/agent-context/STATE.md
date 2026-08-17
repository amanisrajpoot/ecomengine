# Engine state (keep ≤80 lines)

Update this file **in the same PR** as the feature. Replace lines; do not append a changelog.

## Now

| Field | Value |
|-------|--------|
| Checkout | Phase 26 — Playwright PWA E2E |
| API version | `0.17.0` (`backend/app/core/config.py`) |
| Base branch for new work | `cursor/phase-26-playwright-e2e-dfc8` |
| Branch name template | `cursor/<short-name>-dfc8` |
| Browser E2E | Playwright smoke for customer, merchant, rider, admin PWAs |
| Tests | backend **56** + golden **3** + Playwright **12** smoke |

## Next recommended task

Production hardening (rate limits, observability), or merge stacked PR chain to `main`.

## Commands

```bash
pnpm ci                    # backend + golden + typecheck (no browser)
pnpm test:e2e              # Playwright smoke (starts 4 Next dev servers)
pnpm test:golden           # Food + Hyperlocal + Courier only
```

## Last change

- Phase 26: `@commerce/e2e` Playwright package + CI job

## Known constraints

- Playwright smoke does not drive full golden flows (backend integration covers those)
- Map tiles require network; tracking is poll-based
