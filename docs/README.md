# Commerce Engine — Phase 0 Documentation

Agent-executable specifications for the Universal Commerce & Fulfillment Engine.

**Market defaults (V1):** India — INR, GST, Razorpay + COD (later), ONDC as a future adapter.

## Spec index

| Document | Purpose |
|----------|---------|
| [architecture.md](./architecture.md) | Platform layers, modular monolith, stack, V1 exclusions |
| [domain-model.md](./domain-model.md) | Core entities and relationships |
| [schema.md](./schema.md) | PostgreSQL table/column/index specification |
| [order-state-machines.md](./order-state-machines.md) | Configurable order state machines by vertical |
| [pricing-engine.md](./pricing-engine.md) | Pricing pipeline and breakdown contract |
| [tax-engine.md](./tax-engine.md) | India GST tax engine (customer vs platform vs settlement) |
| [settlement-engine.md](./settlement-engine.md) | Ledger-first money movement and settlement lifecycle |
| [fulfillment.md](./fulfillment.md) | Order vs fulfillment, delivery assignment V1 |
| [api-conventions.md](./api-conventions.md) | REST API style, errors, pagination, tenancy |
| [permissions.md](./permissions.md) | Roles and capability matrix |
| [coding-conventions.md](./coding-conventions.md) | Module layout, money, IDs, events, timezones |
| [milestones.md](./milestones.md) | Phased delivery order and golden-flow acceptance |
| [agent-context/](./agent-context/INDEX.md) | Dispatcher: INDEX, STATE, MAP, ROUTES, PHASES, SCHEMA offsets |

## Critical rules

1. **One `Order` model** — never `FoodOrder` / `GroceryOrder` / `CourierOrder`. Verticals configure behavior.
2. **Business `type` enables capabilities** — it does not fork the database schema.
3. **Money is integer paise** — never floating-point currency.
4. **Ledger before settlement** — never compute merchant payout from one giant formula at settlement time.
5. **ONDC is an adapter** — the core domain must not know ONDC exists.
