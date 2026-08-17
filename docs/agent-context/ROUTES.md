# Change routes — pick the change type, open only these

Never discover files by listing the repo. Use the row, then MAP for exact paths.

## Add or change a backend API

1. `backend/app/<module>/schemas.py` — request/response  
2. `backend/app/<module>/service.py` — logic  
3. `backend/app/<module>/router.py` — HTTP  
4. `backend/app/main.py` — `include_router` if new  
5. `backend/app/identity/rbac.py` (when it exists) — permission  
6. `backend/tests/test_phaseN_<name>.py`  
7. `packages/types/src/index.ts` + `packages/api-client/src/index.ts` if UIs will call it  
8. Tick [MAP.md](./MAP.md)

Do **not** open other modules’ routers. Cross-module: call **service**, not ORM.

## Add a table / column

1. [SCHEMA.md](./SCHEMA.md) → `docs/schema.md` **slice only**  
2. `docs/schema.md` (that slice) if the spec must change  
3. `backend/app/<module>/models.py`  
4. `backend/alembic/versions/` (from Phase 1)  
5. Tests that insert that entity  

Do **not** read the rest of schema.md.

## Add a permission / role

1. `docs/permissions.md` (only if the matrix changes)  
2. `backend/app/identity/rbac.py`  
3. The router `require_permission("…")`  
4. Test 403 + 200  

## Add a PWA / admin screen

1. `apps/<app>/app/<route>/page.tsx` (create)  
2. `apps/<app>/components/AppShell.tsx` when nav exists  
3. `packages/api-client/src/index.ts` methods used  
4. `packages/ui/src/<component>.tsx` + barrel `packages/ui/src/index.ts` if shared  
5. Register route in [MAP.md](./MAP.md) Apps table  

Do **not** open the other three apps unless the component is shared.

## Add a shared UI component

1. `packages/ui/src/<name>.tsx`  
2. `packages/ui/src/index.ts`  
3. Importing page only  

Avoid `packages/ui/src/index.tsx` circular imports (import sibling files, not the barrel, from inside `packages/ui`).

## Money / pricing / tax math

1. [RULES.md](./RULES.md)  
2. `docs/pricing-engine.md` **or** `docs/tax-engine.md` (not both unless both change)  
3. `backend/app/pricing/` or `backend/app/taxation/`  
4. Integer paise tests  

## Order status / vertical flow

1. `docs/order-state-machines.md` — **only the profile** (FOOD / HYPERLOCAL / COURIER)  
2. `backend/app/orders/`  
3. Do **not** add a new order table  

## Fulfillment vs delivery

1. `docs/fulfillment.md` relevant heading  
2. `backend/app/fulfillment/` **or** `backend/app/delivery/` **or** `backend/app/partners/` — not all three unless the task spans them  

## Version bump

1. `backend/app/core/config.py` `app_version`  
2. [STATE.md](./STATE.md)  

## Docker / local run

1. `docker-compose.yml`  
2. `.env.example`  
3. `backend/Dockerfile`  

## Docs-only

1. The one spec file  
2. One INDEX row if a new spec path appears  
3. Do not rewrite STATE with essays  

## Implementing the next milestone

Ignore this file’s other rows. Open [PHASES.md](./PHASES.md) for that phase **only**.
