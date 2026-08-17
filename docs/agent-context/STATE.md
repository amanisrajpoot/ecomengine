# Engine state (keep ≤80 lines)

Update this file **in the same PR** as the feature. Replace lines; do not append a changelog.

## Now

| Field | Value |
|-------|--------|
| Checkout | Phase 14 — hyperlocal |
| API version | `0.14.0` (`backend/app/core/config.py`) |
| Base branch for new work | `cursor/phase-14-hyperlocal-dfc8` |
| Branch name template | `cursor/<short-name>-dfc8` |
| API | inventory reserve on pay, consume on deliver, release on cancel |
| Tests | through `test_phase14_hyperlocal.py` (2) — **50 total** |

## Next recommended task

**Phase 15 — Courier.**

Open [PHASES.md](./PHASES.md) Phase 15 section only — do not scan repo.

## Commands

```bash
cd backend && PYTHONPATH=. python3 -m pytest -q
pnpm typecheck
alembic upgrade head   # Postgres / Docker deploy
```

Docker: `cp .env.example .env && docker compose up --build`

## Last change

- Phase 14: Hyperlocal inventory hooks + golden path test through settlement

## Known constraints

- Courier vertical in Phase 15
- Money: integer paise only
- ONDC adapter only in Phase 20
