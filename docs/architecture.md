# Architecture

## Platform layers

```text
┌──────────────────────────────────────────────┐
│              EXPERIENCE LAYER                │
│ Customer PWA │ Merchant PWA │ Rider PWA     │
│ Admin Portal │ Partner Portal (later)        │
└──────────────────────┬───────────────────────┘
                       │
┌──────────────────────▼───────────────────────┐
│               COMMERCE ENGINE                │
│ Catalog │ Cart │ Pricing │ Orders │ Payments│
│ Tax     │ Ledger │ Settlement │ Promotions  │
└──────────────────────┬───────────────────────┘
                       │
┌──────────────────────▼───────────────────────┐
│             FULFILLMENT ENGINE               │
│ Delivery │ Riders │ Vehicles │ Routing      │
│ Tracking │ Assignment │ Pickup │ Drop        │
└──────────────────────────────────────────────┘
```

Later channel adapters (not core):

```text
Commerce Engine
      │
      ├── Direct PWA
      ├── ONDC Adapter
      ├── API Partners
      └── External Marketplaces
```

Money flows are a first-class concern (Ledger + Settlement), conceptually a **Money Engine** fed by commerce and fulfillment events.

## Deployment shape

**Modular monolith** with clean module boundaries under `backend/app/`.

Do **not** start with Kubernetes or microservices.

```text
Docker Compose
  → CI/CD
  → Cloud VM / single deployable
  → PostgreSQL + Redis + S3-compatible object storage
```

## Technology stack

### Frontend

- Next.js (App Router), TypeScript, Tailwind
- PWA (customer, merchant, rider)
- React Query (when screens land)
- Zustand or Redux Toolkit (when client state is needed)
- Maps + WebSockets (fulfillment/tracking phases)

### Backend

- Python, FastAPI
- PostgreSQL
- Redis
- Celery/RQ for background jobs (from Phase 1+)
- WebSockets (delivery tracking)
- S3-compatible object storage (MinIO locally)

### Shared packages

- `packages/types` — shared TypeScript types
- `packages/api-client` — HTTP client against `/api/v1`
- `packages/ui` — shared UI primitives (thin at first)
- `packages/config` — shared TSConfig / tooling

## Module boundaries

Each domain lives in `backend/app/<module>/` and owns:

- models (SQLAlchemy)
- schemas (Pydantic)
- services
- router (API)
- events (publish / handlers)

Cross-module calls go through **service interfaces** or **domain events**, not by reaching into another module’s ORM models from routers.

| Module | Responsibility |
|--------|----------------|
| `core` | Config, DB, Redis, events, shared utilities |
| `identity` | Users, auth, roles |
| `tenants` | Multi-tenancy |
| `businesses` | Business onboarding, capabilities |
| `locations` | Business locations, geo |
| `catalog` | Categories, products, variants, addons, bundles |
| `inventory` | Stock, reservations, movements (optional per business) |
| `cart` | Cart aggregates |
| `pricing` | Price pipeline / breakdown |
| `taxation` | Tax rules and calculation |
| `orders` | Universal order + state machine |
| `payments` | Payment gateway abstraction |
| `ledger` | Double-entry / financial event ledger |
| `settlements` | Merchant / rider / platform payouts |
| `fulfillment` | Fulfillment records decoupled from order |
| `delivery` | Deliveries, stops, tracking |
| `partners` | Delivery partners, vehicles, availability |
| `promotions` | Discounts / offers |
| `notifications` | SMS / push / email fan-out |
| `support` | Tickets / order debugger inputs |
| `reviews` | Ratings |
| `integrations` | ONDC, maps, SMS providers (adapters only) |

## Event architecture

Start with an **in-process event bus** (`backend/app/core/events.py`).

Canonical events (publish early, handlers grow over phases):

- `OrderCreated`
- `PaymentCaptured`
- `OrderAccepted`
- `OrderReady`
- `RiderAssigned`
- `OrderPickedUp`
- `OrderDelivered`
- `OrderCancelled`
- `RefundCreated`
- `SettlementCreated`

Example fan-out:

```text
PaymentCaptured
       │
       ├── OrderService
       ├── NotificationService
       ├── LedgerService
       └── FulfillmentService
```

Kafka/RabbitMQ only if scale requires it later.

## Multi-tenancy

Every relevant entity is scoped with `tenant_id` from day one.

Configuration layers:

- `PlatformConfig`
- `TenantConfig`
- `BusinessConfig`

## Verticals via capabilities

Business types (`FOOD`, `RETAIL`, `GROCERY`, `COURIER`) **do not** dictate table structure.

They enable capabilities, e.g.:

```json
{
  "type": "FOOD",
  "capabilities": {
    "catalog": true,
    "inventory": false,
    "addons": true,
    "delivery": true,
    "scheduledOrders": true
  }
}
```

## V1 explicitly excludes

- Microservices / Kubernetes
- Native Android/iOS apps
- AI recommendations
- Complex route optimization
- Dynamic pricing
- Loyalty ecosystem
- Advanced WMS
- Subscriptions
- Multiple payment gateways (start: one online + COD)
- Multiple map providers
- Full accounting suite
- Analytics warehouse
- Many verticals beyond Food, Hyperlocal, Courier

## North-star philosophy

Build the **generic engine first**; keep verticals thin.

If Food, Hyperlocal, and Courier each reimplement pricing, orders, payments, riders, or settlement, the architecture has failed.
