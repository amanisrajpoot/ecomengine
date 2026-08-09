# Online payments UI (Phase 28)

Cashfree + COD payment experience in the Customer PWA, with admin verify/refund on the order debugger.

## Customer PWA

### Cart checkout
- **Cash on delivery** — same as before (`payment_provider: cod`)
- **Pay online (Cashfree)** — checkout creates order in `PAYMENT_PENDING` with Cashfree session (mock in local dev)

### Order detail
`PaymentPanel` shows when payment is pending:
- Mock mode: **Simulate successful payment** button → calls verify API
- Production: **Pay with Cashfree** link when `payment_url` is present
- Polls every 5 seconds until `PAYMENT_CONFIRMED`

## Admin web

Order debugger includes **Payment actions**:
- **Verify capture** for `PENDING` payments (mock/sandbox)
- **Full refund** for `CAPTURED` payments

## api-client

- `listPaymentProviders`
- `listOrderPayments`
- `initiateOrderPayment`
- `verifyOrderPayment`
- `refundPayment`

## Backend

Payment routes on `/orders/{id}/payments` respect customer order scoping (Phase 25 access helper).

Cashfree runs in **mock mode** when `PAYMENTS_MOCK=true` or credentials are missing (default in local/docker).

## Demo flow

1. Customer PWA → cart → choose **Pay online (Cashfree)**
2. Order detail shows `PAYMENT_PENDING` + **Simulate successful payment**
3. After verify → `PAYMENT_CONFIRMED` → merchant can accept order
4. Admin debugger → verify/refund if needed

## API version

`0.28.0`
