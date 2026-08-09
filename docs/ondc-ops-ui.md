# ONDC ops UI (Phase 32)

Admin console for inspecting Beckn BPP sessions created by the Phase 20 ONDC adapter.

## Admin web

| Route | Purpose |
|-------|---------|
| `/ondc` | Adapter meta + tenant session list with stage filter |
| `/ondc/[sessionId]` | Session detail — transaction, BAP/BPP, cart/order links, callback log |

Session detail links to the order debugger when `order_id` is set.

## Backend

New admin query routes (`ondc.read` — SUPER_ADMIN / TENANT_ADMIN only):

- `GET /api/v1/integrations/ondc/sessions?stage=&limit=`
- `GET /api/v1/integrations/ondc/sessions/{id}`

Existing ingress (`search` → `confirm`) unchanged. `GET /integrations/ondc/meta` remains public.

## Shared UI

`OndcSessionCard` in `@commerce/ui` — stage badge, transaction id, BAP, order/cart hints, callback count.

## api-client

`getOndcMeta`, `listOndcSessions`, `getOndcSession`

## Demo flow

1. Run ONDC golden test or `POST /integrations/ondc/search` with `X-Tenant-ID`
2. **Admin** (:3003) → **ONDC** → see session at `CONFIRM` stage
3. Open session → inspect callback log and link to order debugger

## API version

`0.32.0`
