# Merchant catalog UI (Phase 34)

Product and variant management in the Merchant PWA for businesses with the `catalog` capability.

## Merchant PWA screens

| Route | Purpose |
|-------|---------|
| `/catalog` | Product list — business/category filters, inactive toggle |
| `/catalog/new` | Create product + first variant (optional new category) |
| `/catalog/[productId]` | Edit product, manage variants, toggle availability |

See **Phase 35** (`docs/catalog-addons.md`) for addon management and product-addon linking.

## API usage

New `@commerce/api-client` methods:

- `listCategories`, `createCategory`, `updateCategory`
- `getProduct`, `createProduct`, `updateProduct`
- `createVariant`, `updateVariant`
- `listProducts` now accepts `{ active_only?, category_id? }`
- `createAddon`, `updateAddon`

## Shared UI

- `ProductCard` — product summary with status, variant count, min price
- `VariantRow` — variant line with price and availability badge

## RBAC

Uses existing Phase 3 permissions:

- `catalog.read` — list/browse
- `catalog.manage` — create/update products, variants, categories

Merchant demo user (`merchant@demo.com`) has `BUSINESS_OWNER` with both permissions.

## Demo flow

1. Merchant PWA (:3001) — login as `merchant@demo.com`
2. Open **Catalog** — see Spice Kitchen / FreshMart seeded products
3. **Add product** — create a menu item with price
4. Open product → add another variant or mark unavailable
5. Customer PWA (:3000) — browse store to see changes (active products only)

Courier businesses show an empty state — `catalog` capability is off.

## API version

`0.34.0`
