# Path map (Phase 0)

Do not treat empty `__init__.py` modules as implemented domains.

```
docs/                    Phase 0 specs (source of truth)
docs/agent-context/      Compact index for agents (this folder)
backend/app/main.py      Health + meta only
backend/app/core/        config, db, redis, events
backend/app/<module>/    Empty packages: identity, tenants, businesses,
                         locations, catalog, inventory, cart, pricing,
                         taxation, orders, payments, ledger, settlements,
                         fulfillment, delivery, partners, promotions,
                         notifications, reviews, support, integrations
backend/tests/           test_health.py
apps/customer-pwa        Next shell
apps/merchant-pwa        Next shell
apps/rider-pwa           Next shell
apps/admin-web           Next shell
packages/types           Shared TS types
packages/api-client      HTTP client stub
packages/ui              Shared UI stub
packages/config          TS tooling
docker-compose.yml       API + Postgres + Redis + MinIO
```

When a module grows, grep `backend/app/<module>/router.py` before reading the spec.
