"""Phase 7: orders checkout and state machine transitions."""

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
        json={
            "email": f"{slug}@customer.example.com",
            "password": "CustomerPass123!",
        },
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


async def _food_cart(client: AsyncClient, headers: dict[str, str], slug: str) -> str:
    admin = await _admin_headers(client, headers["X-Tenant-ID"])
    biz = await client.post(
        "/api/v1/businesses",
        headers=admin,
        json={"name": f"Kitchen {slug}", "type": "FOOD", "status": "ACTIVE"},
    )
    business_id = biz.json()["id"]
    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=admin,
        json={"name": "Dal Makhani"},
    )
    product_id = product.json()["id"]
    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product_id}/variants",
        headers=admin,
        json={"name": "Full", "base_price_paise": 22000},
    )
    variant_id = variant.json()["id"]

    cart = await client.post(
        "/api/v1/carts",
        headers=headers,
        json={"business_id": business_id},
    )
    cart_id = cart.json()["id"]
    await client.post(
        f"/api/v1/carts/{cart_id}/items",
        headers=headers,
        json={"variant_id": variant_id, "quantity": 1},
    )
    return cart_id


@pytest.mark.asyncio
async def test_checkout_from_cart(client: AsyncClient) -> None:
    headers = await _tenant_and_customer(client, "p7-checkout")
    cart_id = await _food_cart(client, headers, "p7")

    order = await client.post(
        "/api/v1/orders/checkout",
        headers=headers,
        json={"cart_id": cart_id},
    )
    assert order.status_code == 200, order.text
    body = order.json()
    assert body["status"] == "PAYMENT_PENDING"
    assert body["state_machine_profile"] == "FOOD_DELIVERY"
    assert len(body["items"]) == 1
    assert body["items"][0]["name_snapshot"].startswith("Dal Makhani")
    assert body["pricing_snapshot"]["total_paise"] > 0


@pytest.mark.asyncio
async def test_food_order_state_transitions(client: AsyncClient) -> None:
    headers = await _tenant_and_customer(client, "p7-flow")
    admin = await _admin_headers(client, headers["X-Tenant-ID"])
    cart_id = await _food_cart(client, headers, "p7f")

    checkout = await client.post(
        "/api/v1/orders/checkout",
        headers=headers,
        json={"cart_id": cart_id},
    )
    order_id = checkout.json()["id"]

    confirmed = await client.post(
        f"/api/v1/orders/{order_id}/transition",
        headers=admin,
        json={"to_status": "PAYMENT_CONFIRMED", "reason": "test payment"},
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["status"] == "PAYMENT_CONFIRMED"

    accepted = await client.post(
        f"/api/v1/orders/{order_id}/transition",
        headers=admin,
        json={"to_status": "ACCEPTED"},
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["status"] == "ACCEPTED"
    assert len(accepted.json()["status_events"]) >= 3


@pytest.mark.asyncio
async def test_invalid_transition_rejected(client: AsyncClient) -> None:
    headers = await _tenant_and_customer(client, "p7-bad")
    admin = await _admin_headers(client, headers["X-Tenant-ID"])
    cart_id = await _food_cart(client, headers, "p7b")

    checkout = await client.post(
        "/api/v1/orders/checkout",
        headers=headers,
        json={"cart_id": cart_id},
    )
    order_id = checkout.json()["id"]

    bad = await client.post(
        f"/api/v1/orders/{order_id}/transition",
        headers=admin,
        json={"to_status": "DELIVERED"},
    )
    assert bad.status_code == 400, bad.text
    assert bad.json()["error"]["code"] == "INVALID_TRANSITION"


@pytest.mark.asyncio
async def test_customer_cannot_read_other_order(client: AsyncClient) -> None:
    headers_a = await _tenant_and_customer(client, "p7-own")
    tenant_id = headers_a["X-Tenant-ID"]
    cart_id = await _food_cart(client, headers_a, "own")
    order = await client.post(
        "/api/v1/orders/checkout",
        headers=headers_a,
        json={"cart_id": cart_id},
    )
    order_id = order.json()["id"]

    reg_b = await client.post(
        "/api/v1/auth/register",
        headers={"X-Tenant-ID": tenant_id},
        json={"email": "other7@customer.example.com", "password": "CustomerPass123!"},
    )
    headers_b = {
        "Authorization": f"Bearer {reg_b.json()['access_token']}",
        "X-Tenant-ID": tenant_id,
    }
    denied = await client.get(f"/api/v1/orders/{order_id}", headers=headers_b)
    assert denied.status_code == 403, denied.text
