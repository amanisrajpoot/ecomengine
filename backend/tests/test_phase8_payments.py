"""Phase 8: multi-gateway payments (Cashfree + COD)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.payments.registry import gateway_registry


def test_gateway_registry_includes_cashfree_and_cod() -> None:
    providers = gateway_registry.list_providers()
    assert "cashfree" in providers
    assert "cod" in providers


async def _admin_headers(client: AsyncClient) -> dict[str, str]:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _priced_cart(client: AsyncClient, slug: str):
    headers = await _admin_headers(client)
    tenant = await client.post(
        "/api/v1/tenants", headers=headers, json={"name": slug, "slug": slug}
    )
    headers["X-Tenant-ID"] = tenant.json()["id"]
    biz = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={"name": "Kitchen", "type": "FOOD", "status": "ACTIVE"},
    )
    business_id = biz.json()["id"]
    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=headers,
        json={"name": "Burger"},
    )
    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product.json()['id']}/variants",
        headers=headers,
        json={"name": "Regular", "base_price_paise": 19900},
    )
    cart = await client.post(
        "/api/v1/carts",
        headers=headers,
        json={"business_id": business_id, "delivery_fee_paise": 3000, "platform_fee_paise": 500},
    )
    cart_id = cart.json()["id"]
    await client.post(
        f"/api/v1/carts/{cart_id}/items",
        headers=headers,
        json={"variant_id": variant.json()["id"], "quantity": 1},
    )
    return headers, cart_id


@pytest.mark.asyncio
async def test_list_payment_providers(client: AsyncClient) -> None:
    headers = await _admin_headers(client)
    resp = await client.get("/api/v1/payments/providers", headers=headers)
    assert resp.status_code == 200, resp.text
    assert set(resp.json()["providers"]) >= {"cashfree", "cod"}


@pytest.mark.asyncio
async def test_cod_checkout_confirms_payment(client: AsyncClient) -> None:
    headers, cart_id = await _priced_cart(client, "pay-cod")
    checkout = await client.post(
        "/api/v1/orders/checkout",
        headers=headers,
        json={"cart_id": cart_id, "payment_provider": "cod"},
    )
    assert checkout.status_code == 200, checkout.text
    order = checkout.json()
    assert order["status"] == "PAYMENT_CONFIRMED"
    assert order["payment_method"] == "COD"

    payments = await client.get(f"/api/v1/orders/{order['id']}/payments", headers=headers)
    assert payments.status_code == 200, payments.text
    rows = payments.json()
    assert len(rows) == 1
    assert rows[0]["provider"] == "cod"
    assert rows[0]["status"] == "AUTHORIZED"
    assert rows[0]["amount_paise"] == order["pricing_snapshot"]["total_paise"]


@pytest.mark.asyncio
async def test_cashfree_mock_checkout_verify_and_refund(client: AsyncClient) -> None:
    headers, cart_id = await _priced_cart(client, "pay-cf")
    checkout = await client.post(
        "/api/v1/orders/checkout",
        headers=headers,
        json={
            "cart_id": cart_id,
            "payment_provider": "cashfree",
            "return_url": "https://example.com/return",
            "customer_phone": "9876543210",
        },
    )
    assert checkout.status_code == 200, checkout.text
    order = checkout.json()
    assert order["status"] == "PAYMENT_PENDING"
    assert order["payment_method"] == "ONLINE"
    order_id = order["id"]

    listed = await client.get(f"/api/v1/orders/{order_id}/payments", headers=headers)
    assert listed.status_code == 200
    payment = listed.json()[0]
    assert payment["provider"] == "cashfree"
    assert payment["status"] == "PENDING"
    assert payment["checkout_payload"].get("payment_session_id")
    assert payment["checkout_payload"].get("mode") == "mock"

    verify = await client.post(
        f"/api/v1/orders/{order_id}/payments/verify",
        headers=headers,
        json={"provider": "cashfree", "provider_ref": payment["provider_ref"]},
    )
    assert verify.status_code == 200, verify.text
    assert verify.json()["order_status"] == "PAYMENT_CONFIRMED"
    assert verify.json()["payment"]["status"] == "CAPTURED"

    refund = await client.post(
        f"/api/v1/payments/{payment['id']}/refunds",
        headers=headers,
        json={"amount_paise": 1000, "reason": "customer_request"},
    )
    assert refund.status_code == 200, refund.text
    assert refund.json()["status"] == "REFUNDED"
    assert refund.json()["amount_paise"] == 1000


@pytest.mark.asyncio
async def test_legacy_payment_method_online_uses_cashfree(client: AsyncClient) -> None:
    headers, cart_id = await _priced_cart(client, "pay-legacy-online")
    checkout = await client.post(
        "/api/v1/orders/checkout",
        headers=headers,
        json={"cart_id": cart_id, "payment_method": "ONLINE"},
    )
    assert checkout.status_code == 200, checkout.text
    assert checkout.json()["status"] == "PAYMENT_PENDING"
    payments = await client.get(
        f"/api/v1/orders/{checkout.json()['id']}/payments", headers=headers
    )
    assert payments.json()[0]["provider"] == "cashfree"


@pytest.mark.asyncio
async def test_cashfree_webhook_confirms_payment(client: AsyncClient) -> None:
    headers, cart_id = await _priced_cart(client, "pay-webhook")
    checkout = await client.post(
        "/api/v1/orders/checkout",
        headers=headers,
        json={"cart_id": cart_id, "payment_provider": "cashfree"},
    )
    order_id = checkout.json()["id"]
    payment = (
        await client.get(f"/api/v1/orders/{order_id}/payments", headers=headers)
    ).json()[0]

    webhook = await client.post(
        "/api/v1/webhooks/cashfree",
        json={
            "type": "PAYMENT_SUCCESS",
            "data": {
                "order": {
                    "order_id": payment["provider_ref"],
                    "order_status": "PAID",
                }
            },
        },
    )
    assert webhook.status_code == 200, webhook.text
    assert webhook.json()["status"] == "ok"

    order = await client.get(f"/api/v1/orders/{order_id}", headers=headers)
    assert order.status_code == 200
    assert order.json()["status"] == "PAYMENT_CONFIRMED"


@pytest.mark.asyncio
async def test_unsupported_provider_rejected(client: AsyncClient) -> None:
    headers, cart_id = await _priced_cart(client, "pay-bad-provider")
    # Create order via COD first, then try unsupported initiate on a fresh cart path:
    # checkout with unknown provider should fail at gateway registry.
    checkout = await client.post(
        "/api/v1/orders/checkout",
        headers=headers,
        json={"cart_id": cart_id, "payment_provider": "razorpay"},
    )
    assert checkout.status_code == 400, checkout.text
    assert checkout.json()["error"]["code"] == "PAYMENT_PROVIDER_UNSUPPORTED"
