# Merchant addons UI (Phase 35)

Addon management and product-addon linking — completes the Phase 34 catalog deferral.

## Merchant PWA screens

| Route | Purpose |
|-------|---------|
| `/catalog/addons` | Create addons, set price/max qty, activate/deactivate |
| `/catalog/[productId]` | Link addons to product (group name, required flag) |

Catalog list header includes **Addons** shortcut.

## API usage

- `linkProductAddon(businessId, productId, { addon_id, group_name?, is_required? })`
- Uses Phase 34 `createAddon`, `updateAddon`, `listAddons`, `listProductAddons`

No unlink API in backend v1 — links are additive only.

## Shared UI

- `AddonCard` — addon name, price, max qty, active status

## Demo flow

1. Merchant → **Catalog** → **Addons** → create "Extra cheese" ₹29
2. Open a food product (e.g. Butter Chicken) → **Link addon**
3. Customer PWA → Spice Kitchen menu → add item → see addon picker

## API version

`0.35.0`
