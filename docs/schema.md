# Schema Specification (PostgreSQL)

Spec only for Phase 0. Migrations land with Phase 1+.

Conventions:

- PK: `id UUID PRIMARY KEY`
- Money: `BIGINT` paise
- Timestamps: `timestamptz` UTC
- Soft deletes optional via `deleted_at`
- All tenant-owned tables include `tenant_id UUID NOT NULL`

---

## tenancy & config

### tenants

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| name | TEXT | |
| slug | TEXT UNIQUE | |
| status | TEXT | ACTIVE/SUSPENDED |
| config | JSONB | TenantConfig |
| created_at, updated_at | timestamptz | |

### platform_config

| Column | Type |
|--------|------|
| id | UUID PK |
| key | TEXT UNIQUE |
| value | JSONB |
| updated_at | timestamptz |

---

## identity

### users

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| tenant_id | UUID NULL | null for SUPER_ADMIN |
| email | TEXT NULL | |
| phone | TEXT NULL | E.164 |
| password_hash | TEXT NULL | |
| status | TEXT | |
| created_at, updated_at | timestamptz | |

Indexes: unique `(tenant_id, phone)` where phone not null; unique `(tenant_id, email)` where email not null.

### user_role_bindings

| Column | Type |
|--------|------|
| id | UUID PK |
| user_id | UUID |
| tenant_id | UUID NULL |
| business_id | UUID NULL |
| role | TEXT |
| created_at | timestamptz |

Unique: `(user_id, role, tenant_id, business_id)`.

### customer_profiles

| Column | Type |
|--------|------|
| id | UUID PK |
| tenant_id | UUID |
| user_id | UUID UNIQUE |
| display_name | TEXT NULL |
| created_at, updated_at | timestamptz |

### delivery_partner_profiles

| Column | Type |
|--------|------|
| id | UUID PK |
| tenant_id | UUID |
| user_id | UUID UNIQUE |
| status | TEXT |
| is_online | BOOLEAN |
| documents | JSONB |
| current_lat, current_lng | DOUBLE PRECISION NULL |
| service_area | JSONB NULL |
| created_at, updated_at | timestamptz |

### vehicles

| Column | Type |
|--------|------|
| id | UUID PK |
| tenant_id | UUID |
| partner_id | UUID |
| vehicle_type | TEXT |
| registration | TEXT NULL |
| metadata | JSONB |
| created_at, updated_at | timestamptz |

---

## businesses

### businesses

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| tenant_id | UUID | |
| type | TEXT | FOOD/RETAIL/GROCERY/COURIER |
| name | TEXT | |
| description | TEXT NULL | |
| logo_url | TEXT NULL | |
| contact | JSONB | |
| settings | JSONB | BusinessConfig |
| capabilities | JSONB | |
| status | TEXT | |
| created_at, updated_at | timestamptz | |

Index: `(tenant_id, status)`, `(tenant_id, type)`.

### business_locations

| Column | Type |
|--------|------|
| id | UUID PK |
| tenant_id | UUID |
| business_id | UUID |
| name | TEXT |
| address | JSONB |
| lat, lng | DOUBLE PRECISION |
| service_area | JSONB NULL |
| hours | JSONB |
| timezone | TEXT DEFAULT 'Asia/Kolkata' |
| is_active | BOOLEAN |
| created_at, updated_at | timestamptz |

---

## catalog

### categories

| Column | Type |
|--------|------|
| id | UUID PK |
| tenant_id | UUID |
| business_id | UUID |
| parent_id | UUID NULL |
| name | TEXT |
| sort_order | INT |
| is_active | BOOLEAN |
| created_at, updated_at | timestamptz |

### products

| Column | Type |
|--------|------|
| id | UUID PK |
| tenant_id | UUID |
| business_id | UUID |
| category_id | UUID NULL |
| name | TEXT |
| description | TEXT NULL |
| images | JSONB |
| tags | JSONB |
| is_active | BOOLEAN |
| created_at, updated_at | timestamptz |

### variants

| Column | Type |
|--------|------|
| id | UUID PK |
| tenant_id | UUID |
| product_id | UUID |
| name | TEXT |
| sku | TEXT NULL |
| base_price_paise | BIGINT |
| is_available | BOOLEAN |
| metadata | JSONB |
| created_at, updated_at | timestamptz |

### addons

| Column | Type |
|--------|------|
| id | UUID PK |
| tenant_id | UUID |
| business_id | UUID |
| name | TEXT |
| price_paise | BIGINT |
| max_qty | INT |
| is_active | BOOLEAN |
| created_at, updated_at | timestamptz |

### product_addon_links

| Column | Type |
|--------|------|
| product_id | UUID |
| addon_id | UUID |
| group_name | TEXT NULL |
| is_required | BOOLEAN |

### bundles

| Column | Type |
|--------|------|
| id | UUID PK |
| tenant_id | UUID |
| business_id | UUID |
| name | TEXT |
| price_paise | BIGINT NULL |
| items | JSONB |
| is_active | BOOLEAN |
| created_at, updated_at | timestamptz |

---

## inventory

### inventory_items

| Column | Type |
|--------|------|
| id | UUID PK |
| tenant_id | UUID |
| business_id | UUID |
| location_id | UUID |
| variant_id | UUID |
| on_hand | INT |
| reserved | INT |
| low_stock_threshold | INT NULL |
| updated_at | timestamptz |

Unique: `(location_id, variant_id)`.

Check: `on_hand >= 0`, `reserved >= 0`, `on_hand >= reserved`.

### stock_movements

| Column | Type |
|--------|------|
| id | UUID PK |
| tenant_id | UUID |
| inventory_item_id | UUID |
| reason | TEXT |
| delta_on_hand | INT |
| delta_reserved | INT |
| reference_type | TEXT NULL |
| reference_id | UUID NULL |
| created_at | timestamptz |
| created_by | UUID NULL |

---

## cart & orders

### carts

| Column | Type |
|--------|------|
| id | UUID PK |
| tenant_id | UUID |
| customer_id | UUID |
| business_id | UUID NULL |
| location_id | UUID NULL |
| currency | TEXT DEFAULT 'INR' |
| pricing_snapshot | JSONB |
| created_at, updated_at | timestamptz |

### cart_items

| Column | Type |
|--------|------|
| id | UUID PK |
| cart_id | UUID |
| variant_id | UUID NULL |
| bundle_id | UUID NULL |
| quantity | INT |
| addons | JSONB |
| unit_price_paise | BIGINT |
| metadata | JSONB |

### orders

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| tenant_id | UUID | |
| customer_id | UUID | |
| business_id | UUID NULL | nullable for pure courier |
| location_id | UUID NULL | |
| status | TEXT | |
| state_machine_profile | TEXT | |
| currency | TEXT | INR |
| pricing_snapshot | JSONB | frozen |
| fulfillment_type | TEXT | |
| placed_at | timestamptz | |
| created_at, updated_at | timestamptz | |

Indexes: `(tenant_id, status)`, `(tenant_id, customer_id)`, `(tenant_id, business_id)`.

### order_items

| Column | Type |
|--------|------|
| id | UUID PK |
| order_id | UUID |
| variant_id | UUID NULL |
| name_snapshot | TEXT |
| quantity | INT |
| unit_price_paise | BIGINT |
| addons_snapshot | JSONB |
| metadata | JSONB |

### order_status_events

| Column | Type |
|--------|------|
| id | UUID PK |
| order_id | UUID |
| from_status | TEXT NULL |
| to_status | TEXT |
| actor_user_id | UUID NULL |
| reason | TEXT NULL |
| created_at | timestamptz |

---

## payments

### payments

| Column | Type |
|--------|------|
| id | UUID PK |
| tenant_id | UUID |
| order_id | UUID |
| provider | TEXT |
| provider_ref | TEXT NULL |
| status | TEXT |
| amount_paise | BIGINT |
| currency | TEXT |
| idempotency_key | TEXT NULL |
| raw | JSONB |
| checkout_payload | JSONB |
| created_at, updated_at | timestamptz |

Unique: `(tenant_id, idempotency_key)` where key not null.

### refunds

| Column | Type |
|--------|------|
| id | UUID PK |
| tenant_id | UUID |
| payment_id | UUID |
| order_id | UUID |
| provider_ref | TEXT NULL |
| amount_paise | BIGINT |
| status | TEXT |
| reason | TEXT NULL |
| raw | JSONB |
| created_at, updated_at | timestamptz |

---

## tax

### tax_rules

| Column | Type |
|--------|------|
| id | UUID PK |
| tenant_id | UUID NULL |
| code | TEXT |
| category | TEXT |
| jurisdiction | TEXT |
| rate_bps | INT |
| inclusive | BOOLEAN |
| payer | TEXT |
| kind | TEXT |
| effective_from | timestamptz |
| effective_to | timestamptz NULL |
| created_at, updated_at | timestamptz |

---

## ledger & settlements

### ledger_entries

| Column | Type |
|--------|------|
| id | UUID PK |
| tenant_id | UUID |
| order_id | UUID NULL |
| event_group_id | UUID |
| event_type | TEXT |
| account | TEXT |
| direction | TEXT |
| amount_paise | BIGINT |
| currency | TEXT |
| metadata | JSONB |
| created_at | timestamptz |

Indexes: `(tenant_id, order_id)`, `(tenant_id, account)`, `(event_group_id)`.

### settlements

| Column | Type |
|--------|------|
| id | UUID PK |
| tenant_id | UUID |
| party_type | TEXT |
| party_id | UUID |
| status | TEXT |
| period_start, period_end | timestamptz |
| total_paise | BIGINT |
| currency | TEXT |
| report | JSONB |
| created_at, updated_at | timestamptz |

### settlement_ledger_links

| Column | Type |
|--------|------|
| settlement_id | UUID |
| ledger_entry_id | UUID |

---

## fulfillment & delivery

### fulfillments

| Column | Type |
|--------|------|
| id | UUID PK |
| tenant_id | UUID |
| order_id | UUID UNIQUE |
| type | TEXT |
| status | TEXT |
| scheduled_for | timestamptz NULL |
| metadata | JSONB |
| created_at, updated_at | timestamptz |

### deliveries

| Column | Type |
|--------|------|
| id | UUID PK |
| tenant_id | UUID |
| fulfillment_id | UUID |
| partner_id | UUID NULL |
| vehicle_id | UUID NULL |
| status | TEXT |
| eta | timestamptz NULL |
| created_at, updated_at | timestamptz |

### delivery_stops

| Column | Type |
|--------|------|
| id | UUID PK |
| delivery_id | UUID |
| sequence | INT |
| stop_type | TEXT |
| address | JSONB |
| lat, lng | DOUBLE PRECISION |
| contact | JSONB |
| status | TEXT |
| proof | JSONB NULL |
| completed_at | timestamptz NULL |

---

## promotions (stub)

### promotions

| Column | Type |
|--------|------|
| id | UUID PK |
| tenant_id | UUID |
| business_id | UUID NULL |
| code | TEXT NULL |
| rules | JSONB |
| is_active | BOOLEAN |
| created_at, updated_at | timestamptz |

---

## Notes

- No `food_orders` / `grocery_orders` / `courier_orders` tables.
- Courier package details live in `orders.pricing_snapshot` / `fulfillments.metadata` / item metadata.
- Foreign keys to be added in Alembic migrations when modules are implemented.
