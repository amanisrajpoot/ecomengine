# Customer journey (Phase 25)

End-to-end customer experience: delivery address at checkout, scoped order history, live tracking, and self-service cancel.

## Checkout address

Customer cart checkout sends `delivery_address` on `POST /orders/checkout`. The backend stores it on order metadata as `drop`:

```json
{
  "drop": {
    "lat": 12.9352,
    "lng": 77.6245,
    "address": {
      "line1": "Koramangala 5th Block",
      "city": "Bengaluru",
      "state": "Karnataka",
      "pincode": "560038"
    },
    "contact": { "phone": "9876543210" }
  }
}
```

Fulfillment copies `order.metadata.drop` → `dropoff` when creating fulfillment. Delivery stops use this for the drop location.

The Customer PWA persists the last address in `localStorage` and pre-fills cart + courier drop fields.

## Scoped “my orders”

`GET /orders` auto-scopes to the logged-in customer when the user has only the `CUSTOMER` role. Staff roles (merchant, admin, rider) still see tenant-wide lists unless they pass `mine=true`.

`GET /orders/{id}` returns 404 when a customer-only user requests another customer's order.

## Order tracking

`OrderTrackingPanel` in `@commerce/ui` polls fulfillment + delivery status every 5 seconds on the customer order detail page. Shows rider assignment when available.

## Customer cancel

Customers can cancel early statuses (`PAYMENT_PENDING`, `PAYMENT_CONFIRMED`, `ACCEPTED`) via `POST /orders/{id}/transitions` with `actor: "customer"`.

The api-client `transitionOrder` now respects the `actor` field in the request body.

## Demo flow

1. Log in as `customer@demo.com` on the Customer PWA (port 3000).
2. Add items to cart → enter delivery address → COD checkout.
3. Open **My orders** — only your orders appear.
4. On order detail, watch fulfillment/delivery tracking update after merchant marks **Ready**.
5. Cancel a fresh order before the merchant accepts it.

## API version

`0.25.0`
