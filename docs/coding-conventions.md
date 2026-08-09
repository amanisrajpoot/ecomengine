# Coding Conventions

## Repository

- Modular monolith monorepo
- Backend domain code only under `backend/app/<module>/`
- Do not create vertical-specific order tables or microservices in V1

## Python / FastAPI

- Python 3.12+
- SQLAlchemy 2.x style
- Pydantic v2 schemas
- Routers are thin; business logic in services
- One module = models + schemas + service + router (+ events handlers)

Suggested module file layout:

```text
backend/app/orders/
  __init__.py
  models.py
  schemas.py
  service.py
  router.py
  states.py
```

## TypeScript / Next.js

- App Router
- Shared types from `@commerce/types`
- API calls via `@commerce/api-client`
- Keep PWAs configuration-driven; hide features by capabilities

## Identifiers

- UUID v4 primary keys (`uuid`)
- External-facing ids remain UUIDs (no serial leakage)

## Money

- Store and compute as **integer paise**
- Field names: `*_paise`
- Never use float for currency
- Currency code `INR` for V1

## Time

- Persist UTC (`timestamptz`)
- Default business timezone `Asia/Kolkata`
- API responses ISO-8601 UTC

## Tenancy

- Column `tenant_id` on all tenant-owned tables
- Every query filters by tenant unless platform-scoped super-admin path

## Events

- Past-tense domain names: `OrderCreated`, `PaymentCaptured`
- Payload includes `tenant_id`, aggregate id, and minimal data (handlers reload if needed)
- In-process bus first (`core.events`)

## State machines

- Profiles registered in code/config
- Persist `status` + `state_machine_profile` on orders
- Append-only status history table

## Logging & errors

- Structured logs with `request_id`, `tenant_id`
- Domain errors map to API error codes (see api-conventions)

## Testing

- Unit-test pricing, tax, state transitions, inventory math, ledger, settlement, assignment
- Integration golden paths per vertical (see milestones)
- Money assertions exact (integer)

## Docs before forks

If a change invents a new order type table or food-only payment path, stop — update domain docs and keep the engine generic.
