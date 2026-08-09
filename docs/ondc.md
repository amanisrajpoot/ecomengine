# ONDC adapter

The ONDC integration is an **adapter** under `backend/app/integrations/ondc/`. Core modules (`orders`, `catalog`, `cart`, etc.) do not import ONDC code.

## Role

This deployment acts as a **BPP (seller app)** for retail/food catalog flows:

| Beckn action | Internal mapping |
|--------------|------------------|
| `search` | `discover_nearby_stores` + catalog variants |
| `select` | Persist selected offer lines on `ondc_sessions` |
| `init` | Create cart + price quote |
| `confirm` | `checkout_from_cart` (COD) → internal `Order` |
| `status` | Read order state (mapped to Beckn order state) |
| `cancel` | Order transition → `CANCELLED` |

Offer IDs use the format `ce:{business_id}:{location_id}:{variant_id}`.

## Endpoints

- `GET /api/v1/integrations/ondc/meta` — adapter capabilities and mock flag
- `POST /api/v1/integrations/ondc/{search,select,init,confirm,status,cancel}` — Beckn ingress

## Tenant resolution

- **Mock mode (`ONDC_MOCK=true`, default):** require `X-Tenant-ID` on every request.
- **Production:** resolve tenant from `tenant.config.ondc.bpp_id` matching `context.bpp_id`, plus subscriber auth (Authorization header required when mock is off).

## Sessions

`ondc_sessions` links `transaction_id` → `cart_id` / `order_id` and stores callback payloads in `callback_log` when mock callbacks are enabled.

## Order status callbacks

On domain events (`OrderStatusChanged`, etc.), the adapter appends an `on_status` payload to the session log. Set `ONDC_SEND_CALLBACKS=true` to POST to the BAP URI (signing not yet implemented).

## Local test

```bash
cd backend && PYTHONPATH=. pytest tests/test_phase20_ondc.py -q
```
