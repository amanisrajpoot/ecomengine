# Domain Model

## Critical rule

There is a single **`Order`** aggregate.

Do **not** create `FoodOrder`, `GroceryOrder`, or `CourierOrder`. Verticals configure order behavior via business capabilities and state-machine profiles.

Business `type` enables **capabilities**; it does not fork the schema.

---

## Identity & tenancy

### Tenant

Top-level isolation boundary for the platform.

| Field (logical) | Notes |
|-----------------|-------|
| `id` | UUID |
| `name` | Display name |
| `slug` | Unique |
| `status` | `ACTIVE` / `SUSPENDED` |
| `config` | `TenantConfig` JSON |

### User

Authentication principal.

| Field | Notes |
|-------|-------|
| `id` | UUID |
| `tenant_id` | Nullable only for platform super-admins |
| `email` | Optional |
| `phone` | E.164; primary for India OTP |
| `password_hash` | Optional (OTP-first) |
| `status` | `ACTIVE` / `DISABLED` |

### Role bindings

A user may hold one or more roles in context:

| Role | Scope |
|------|-------|
| `SUPER_ADMIN` | Platform |
| `TENANT_ADMIN` | Tenant |
| `BUSINESS_OWNER` | Business |
| `BUSINESS_MANAGER` | Business |
| `STAFF` | Business / location |
| `DELIVERY_PARTNER` | Tenant (rider) |
| `CUSTOMER` | Tenant |

### Profile types (logical views)

- **Customer** — linked to `User`, addresses, wallet later
- **Merchant** — owner/manager of one or more `Business`
- **DeliveryPartner** — rider profile, documents, availability
- **Staff** — business/location workers
- **Admin** — tenant or platform admin

---

## Business & location

### Business

| Field | Notes |
|-------|-------|
| `id` | UUID |
| `tenant_id` | Required |
| `type` | `FOOD` \| `RETAIL` \| `GROCERY` \| `COURIER` |
| `name`, `description`, `logo_url` | |
| `contact` | Phone / email JSON |
| `settings` | `BusinessConfig` |
| `capabilities` | Derived/override map from type |
| `status` | `DRAFT` / `ACTIVE` / `PAUSED` |

### BusinessLocation

| Field | Notes |
|-------|-------|
| `id` | UUID |
| `tenant_id`, `business_id` | |
| `name` | |
| `address` | Structured address (India) |
| `geo` | lat/lng |
| `service_area` | Optional polygon / radius |
| `hours` | Opening hours JSON |
| `timezone` | Default `Asia/Kolkata` |

---

## Catalog

```text
Catalog (per business / location)
 └── Categories
       └── Products
             └── Variants
             └── Addons (optional)
             └── Bundles / Combos (optional)
```

### Category

Hierarchical optional; `business_id`, `parent_id`, `name`, `sort_order`, `is_active`.

### Product

| Field | Notes |
|-------|-------|
| `business_id`, `category_id` | |
| `name`, `description` | |
| `images` | Object storage keys |
| `is_active` | |
| `tags` | Optional |

### Variant

SKU-bearing sellable unit.

| Field | Notes |
|-------|-------|
| `product_id` | |
| `name` | e.g. Large, Medium |
| `sku` | Optional unless inventory enabled |
| `base_price_paise` | Integer |
| `is_available` | |

### Addon

Optional modifiers (food-heavy, reusable elsewhere).

- `price_paise`, `max_qty`, `is_required` group support

### Bundle / Combo

Collection of variants/addons sold as one line with its own pricing rules.

---

## Inventory (optional)

Enabled when `capabilities.inventory = true`.

| Concept | Rule |
|---------|------|
| `on_hand` | Physical stock |
| `reserved` | Soft-held for carts/orders |
| `available` | `on_hand - reserved` |
| `StockMovement` | **Required** for every mutation |

Never mutate stock without a movement row.

---

## Cart

```text
Cart
 ├── Items (variant + addons + qty)
 ├── Subtotal
 ├── Discounts
 ├── Taxes
 ├── Fees
 ├── Delivery
 └── Total
```

Cart is tenant + customer (+ optional business) scoped. Pricing is computed via the pricing engine; cart stores the latest breakdown snapshot.

---

## Order

Universal order:

```text
Order
 ├── Customer
 ├── Business (+ location)
 ├── Items (frozen snapshot)
 ├── Pricing Snapshot
 ├── Payment
 ├── Fulfillment
 └── Status (state machine)
```

Order items freeze product/variant/addon names and unit prices at checkout time.

---

## Payments

| Entity | Notes |
|--------|-------|
| `Payment` | Intent / capture against an order |
| `Refund` | Partial or full |

Providers (V1): one online gateway (Razorpay) + COD. Abstracted behind `PaymentGateway`.

---

## Money

| Entity | Notes |
|--------|-------|
| `LedgerEntry` | Immutable financial event lines |
| `Settlement` | Aggregated payout batch for merchant / rider / platform |

See [settlement-engine.md](./settlement-engine.md).

---

## Fulfillment & delivery

```text
Order
  │
  ▼
Fulfillment  (DELIVERY | PICKUP | SELF_PICKUP | SCHEDULED | MULTI_STOP)
  │
  ▼
Delivery (optional)
 ├── DeliveryStop(s)
 ├── Partner
 ├── Vehicle
 ├── ETA
 └── Tracking
```

### DeliveryPartner

Documents, availability, `current_location`, service areas.

### Vehicle

Type (`BIKE`, `SCOOTER`, `CAR`, …), registration, linked partner.

---

## Entity relationship sketch

```text
Tenant
  ├── Users / RoleBindings
  ├── Businesses
  │     ├── Locations
  │     ├── Catalog (Categories → Products → Variants / Addons / Bundles)
  │     └── Inventory (optional)
  ├── Customers
  ├── DeliveryPartners → Vehicles
  ├── Carts → Orders → Payments / Refunds
  ├── Fulfillments → Deliveries → Stops
  ├── LedgerEntries
  └── Settlements
```
