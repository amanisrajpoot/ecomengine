"""Phase 28: online payments UI — customer scoping on order payments."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _admin_headers(client: AsyncClient) -> dict[str, str]:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _customer_headers(client: AsyncClient, tenant_id: str, email: str) -> dict[str, str]:
    registered = await client.post(
        "/api/v1/auth/register",
        headers={"X-Tenant-ID": tenant_id},
        json={"email": email, "password": "Customer123!", "display_name": "Cust"},
    )
    assert registered.status_code == 200, registered.text
    return {
        "Authorization": f"Bearer {registered.json()['access_token']}",
        "X-Tenant-ID": tenant_id,
    }


async def _setup_tenant(
    client: AsyncClient, admin: dict[str, str], slug: str
) -> dict[str, str]:
    tenant = await client.post(
        "/api/v1/tenants",
        headers=admin,
        json={"name": slug, "slug": slug},
    )
    headers = {**admin, "X-Tenant-ID": tenant.json()["id"]}
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
    headers["_business_id"] = business_id
    headers["_variant_id"] = variant.json()["id"]
    return headers


async def _customer_cart(
    client: AsyncClient, cust: dict[str, str], setup: dict[str, str]
) -> str:
    cart = await client.post(
        "/api/v1/carts",
        headers=cust,
        json={"business_id": setup["_business_id"], "delivery_fee_paise": 3000},
    )
    await client.post(
        f"/api/v1/carts/{cart.json()['id']}/items",
        headers=cust,
        json={"variant_id": setup["_variant_id"], "quantity": 1},
    )
    return cart.json()["id"]


@pytest.mark.asyncio
async def test_customer_cannot_read_other_order_payments(client: AsyncClient) -> None:
    admin = await _admin_headers(client)
    setup = await _setup_tenant(client, admin, "p28-pay")
    tenant_id = setup["X-Tenant-ID"]

    cust_a = await _customer_headers(client, tenant_id, "pay-a@example.com")
    cust_b = await _customer_headers(client, tenant_id, "pay-b@example.com")

    cart_a = await _customer_cart(client, cust_a, setup)
    order_a = await client.post(
        "/api/v1/orders/checkout",
        headers=cust_a,
        json={"cart_id": cart_a, "payment_provider": "cashfree"},
    )
    assert order_a.status_code == 200, order_a.text
    order_a_id = order_a.json()["id"]

    cart_b = await _customer_cart(client, cust_b, setup)
    order_b = await client.post(
        "/api/v1/orders/checkout",
        headers=cust_b,
        json={"cart_id": cart_b, "payment_provider": "cod"},
    )
    assert order_b.status_code == 200, order_b.text

    own = await client.get(f"/api/v1/orders/{order_a_id}/payments", headers=cust_a)
    assert own.status_code == 200
    assert len(own.json()) == 1

    peek = await client.get(
        f"/api/v1/orders/{order_b.json()['id']}/payments", headers=cust_a
    )
    assert peek.status_code == 404


@pytest.mark.asyncio
async def test_customer_can_verify_mock_cashfree_payment(client: AsyncClient) -> None:
    admin = await _admin_headers(client)
    setup = await _setup_tenant(client, admin, "p28-verify")
    tenant_id = setup["X-Tenant-ID"]
    cust = await _customer_headers(client, tenant_id, "pay-verify@example.com")
    cart_id = await _customer_cart(client, cust, setup)

    checkout = await client.post(
        "/api/v1/orders/checkout",
        headers=cust,
        json={"cart_id": cart_id, "payment_provider": "cashfree"},
    )
    assert checkout.status_code == 200, checkout.text
    order_id = checkout.json()["id"]
    assert checkout.json()["status"] == "PAYMENT_PENDING"

    payment = (await client.get(f"/api/v1/orders/{order_id}/payments", headers=cust)).json()[0]
    verify = await client.post(
        f"/api/v1/orders/{order_id}/payments/verify",
        headers=cust,
        json={"provider": "cashfree", "provider_ref": payment["provider_ref"]},
    )
    assert verify.status_code == 200, verify.text
    assert verify.json()["order_status"] == "PAYMENT_CONFIRMED"
    assert verify.json()["payment"]["status"] == "CAPTURED"
