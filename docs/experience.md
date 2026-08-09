# Experience polish (Phase 23)

Light UX improvements across the four frontends — no new backend domains, no maps/WebSockets.

## Shared UI (`@commerce/ui`)

| Component | Purpose |
|-----------|---------|
| `Spinner` | Loading states |
| `EmptyState` | Zero-data screens with optional CTA |
| `StatusBadge` | Human-readable order/delivery status chips |
| `PriceBreakdown` | Subtotal, fees, tax, total from `pricing_snapshot` |
| `OrderStatusStepper` | Customer/merchant progress for Food, Hyperlocal, Courier profiles |

## Customer PWA

- **Tenant ID** — auto-filled from `NEXT_PUBLIC_TENANT_ID` (written by `pnpm demo:seed`); field hidden when set
- **Cart** — quantity +/- and remove; price breakdown; phone number for COD checkout (remembered in browser)
- **Menu** — optional add-on picker when product has linked addons
- **Order detail** — status stepper + 5s polling until terminal state
- **Nav** — cart item count badge

## Merchant PWA

- **Kitchen board** — card grid with status badges; auto-refresh every 8s
- **Order detail** — stepper + labeled transition buttons (including `PICKING` for hyperlocal)

## Rider PWA

- **Jobs** — online/offline panel; richer job cards with next stop; 10s refresh
- **Delivery detail** — vertical step flow with OTP input per stop (demo OTPs shown)

## Admin web

- **Home** — tenant / order / active-order counts when tenant context is set
- **Tenants** — copy tenant ID; active tenant banner
- **Debugger** — collapsible JSON sections (Order open by default)

## API client additions

- `updateCartItem`, `removeCartItem`
- `listAddons`, `listProductAddons`
