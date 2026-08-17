# Engine state (keep ≤80 lines)

Update this file **in the same PR** as the feature. Replace lines; do not append a changelog.

## Now

| Field | Value |
|-------|--------|
| Checkout | Phase 6 — tax |
| API version | `0.6.0` (`backend/app/core/config.py`) |
| Base branch for new work | `cursor/phase-6-tax-dfc8` |
| Branch name template | `cursor/<short-name>-dfc8` |
| API | through taxation + pricing uses real GST |
| Tests | through `test_phase6_tax.py` (4) — **26 total** |

## Next recommended task

**Phase 7 — Orders.**

Open [PHASES.md](./PHASES.md) Phase 7 section only — do not scan repo.

## Commands

```bash
cd backend && PYTHONPATH=. python3 -m pytest -q
pnpm typecheck
alembic upgrade head   # Postgres / Docker deploy
```

Docker: `cp .env.example .env && docker compose up --build`

## Last change

- Phase 6: tax_rules, CGST/SGST calculation, pricing integration

## Known constraints

- One `Order` model when Phase 7 lands
- Money: integer paise when pricing exists
- ONDC adapter only in Phase 20
