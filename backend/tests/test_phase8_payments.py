"""Phase 8: payments COD, Razorpay stub, refunds, idempotency."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _tenant_and_customer(client: AsyncClient, slug: str) -> dict[str, str]:
    admin_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
    tenant = await client.post(
        "/api/v1/tenants",
        headers=admin_headers,
        json={"name": slug, "slug": slug},
    )
    tenant_id = tenant.json()["id"]
    reg = await client.post(
        "/api/v1/auth/register",
        headers={"X-Tenant-ID": tenant_id},
        json={"email": f"{slug}@customer.example.com", "password": "CustomerPass123!"},
    )
    return {
        "Authorization": f"Bearer {reg.json()['access_token']}",
        "X-Tenant-ID": tenant_id,
    }


async def _admin_headers(client: AsyncClient, tenant_id: str) -> dict[str, str]:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    return {
        "Authorization": f"Bearer {login.json()['access_token']}",
        "X-Tenant-ID": tenant_id,
    }


async def _checkout_order(client: AsyncClient, headers: dict[str, str], slug: str) -> str:
    admin = await _admin_headers(client, headers["X-Tenant-ID"])
    biz = await client.post(
        "/api/v1/businesses",
        headers=admin,
        json={"name": f"Pay {slug}", "type": "FOOD", "status": "ACTIVE"},
    )
    business_id = biz.json()["id"]
    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=admin,
        json={"name": "Biryani"},
    )
    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product.json()['id']}/variants",
        headers=admin,
        json={"name": "Full", "base_price_paise": 25000},
    )
    cart = await client.post(
        "/api/v1/carts",
        headers=headers,
        json={"business_id": business_id},
    )
    cart_id = cart.json()["id"]
    await client.post(
        f"/api/v1/carts/{cart_id}/items",
        headers=headers,
        json={"variant_id": variant.json()["id"], "quantity": 1},
    )
    order = await client.post(
        "/api/v1/orders/checkout",
        headers=headers,
        json={"cart_id": cart_id},
    )
    assert order.status_code == 200, order.text
    return order.json()["id"]


@pytest.mark.asyncio
async def test_cod_payment_confirms_order(client: AsyncClient) -> None:
    headers = await _tenant_and_customer(client, "p8-cod")
    order_id = await _checkout_order(client, headers, "cod")

    pay = await client.post(
        f"/api/v1/orders/{order_id}/payments",
        headers={**headers, "Idempotency-Key": "cod-key-1"},
        json={"provider": "COD"},
    )
    assert pay.status_code == 200, pay.text
    assert pay.json()["status"] == "CAPTURED"
    assert pay.json()["provider"] == "COD"

    order = await client.get(f"/api/v1/orders/{order_id}", headers=headers)
    assert order.status_code == 200, order.text
    assert order.json()["status"] == "PAYMENT_CONFIRMED"


@pytest.mark.asyncio
async def test_payment_idempotency(client: AsyncClient) -> None:
    headers = await _tenant_and_customer(client, "p8-idem")
    order_id = await _checkout_order(client, headers, "idem")
    key = "idem-key-abc"

    first = await client.post(
        f"/api/v1/orders/{order_id}/payments",
        headers={**headers, "Idempotency-Key": key},
        json={"provider": "COD"},
    )
    second = await client.post(
        f"/api/v1/orders/{order_id}/payments",
        headers={**headers, "Idempotency-Key": key},
        json={"provider": "COD"},
    )
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json()["id"] == second.json()["id"]


@pytest.mark.asyncio
async def test_razorpay_capture_flow(client: AsyncClient) -> None:
    headers = await _tenant_and_customer(client, "p8-rzp")
    admin = await _admin_headers(client, headers["X-Tenant-ID"])
    order_id = await _checkout_order(client, headers, "rzp")

    init = await client.post(
        f"/api/v1/orders/{order_id}/payments",
        headers={**headers, "Idempotency-Key": "rzp-key-1"},
        json={"provider": "RAZORPAY"},
    )
    assert init.status_code == 200, init.text
    assert init.json()["status"] == "PENDING"
    assert init.json()["client_payload"]["provider"] == "RAZORPAY"
    payment_id = init.json()["id"]

    captured = await client.post(
        f"/api/v1/payments/{payment_id}/capture",
        headers=admin,
    )
    assert captured.status_code == 200, captured.text
    assert captured.json()["status"] == "CAPTURED"

    order = await client.get(f"/api/v1/orders/{order_id}", headers=headers)
    assert order.json()["status"] == "PAYMENT_CONFIRMED"


@pytest.mark.asyncio
async def test_refund_on_captured_payment(client: AsyncClient) -> None:
    headers = await _tenant_and_customer(client, "p8-refund")
    admin = await _admin_headers(client, headers["X-Tenant-ID"])
    order_id = await _checkout_order(client, headers, "ref")

    pay = await client.post(
        f"/api/v1/orders/{order_id}/payments",
        headers={**headers, "Idempotency-Key": "refund-key"},
        json={"provider": "COD"},
    )
    payment_id = pay.json()["id"]

    refund = await client.post(
        f"/api/v1/payments/{payment_id}/refunds",
        headers=admin,
        json={"reason": "customer request"},
    )
    assert refund.status_code == 200, refund.text
    assert refund.json()["status"] == "COMPLETED"
    assert refund.json()["amount_paise"] == pay.json()["amount_paise"]

    payment = await client.get(f"/api/v1/payments/{payment_id}", headers=admin)
    assert payment.json()["status"] == "REFUNDED"
