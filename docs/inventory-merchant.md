# Inventory merchant UI (Phase 26)

Stock management in the Merchant PWA for grocery/retail businesses with the `inventory` capability.

## Merchant PWA screens

| Route | Purpose |
|-------|---------|
| `/inventory` | Stock board — business/location filters, low/OOS chips, item cards |
| `/inventory/new` | Link catalog variant to location |
| `/inventory/[itemId]` | Receive/adjust stock, movement history |

## API usage

Uses existing Phase 4 inventory endpoints via `@commerce/api-client`:

- `listLocations`, `listInventory`, `upsertInventoryItem`
- `getInventoryItem`, `adjustInventory`, `listInventoryMovements`

## RBAC

- `inventory.manage` — stock mutations (OWNER, MANAGER, STAFF)
- `locations.read` — list locations for inventory UI (added Phase 26; includes STAFF)

## Demo flow

1. Merchant PWA (:3001) — login as `merchant@demo.com`
2. Switch business to **FreshMart Indiranagar** (GROCERY)
3. Open **Inventory** — see Milk 1L (50 available from seed)
4. Tap item → **Receive** or **Adjust** → check movement history

Food businesses (Spice Kitchen) show an empty state — inventory capability is off.

## API version

`0.26.0`
