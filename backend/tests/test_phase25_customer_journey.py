"""Phase 25: customer journey — scoped orders, checkout address, cancel."""

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


async def _food_cart(
    client: AsyncClient,
    headers: dict[str, str],
    slug: str,
) -> str:
    tenant = await client.post(
        "/api/v1/tenants",
        headers=headers,
        json={"name": slug, "slug": slug},
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
    await client.post(
        f"/api/v1/carts/{cart.json()['id']}/items",
        headers=headers,
        json={"variant_id": variant.json()["id"], "quantity": 1},
    )
    return cart.json()["id"]


@pytest.mark.asyncio
async def test_checkout_stores_delivery_address_in_metadata(client: AsyncClient) -> None:
    admin = await _admin_headers(client)
    cart_id = await _food_cart(client, admin, "p25-address")
    checkout = await client.post(
        "/api/v1/orders/checkout",
        headers=admin,
        json={
            "cart_id": cart_id,
            "payment_provider": "cod",
            "customer_phone": "9876543210",
            "delivery_address": {
                "line1": "12 Koramangala",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pincode": "560038",
                "lat": 12.9352,
                "lng": 77.6245,
            },
        },
    )
    assert checkout.status_code == 200, checkout.text
    drop = checkout.json()["metadata"]["drop"]
    assert drop["address"]["line1"] == "12 Koramangala"
    assert drop["lat"] == 12.9352
    assert drop["contact"]["phone"] == "9876543210"


@pytest.mark.asyncio
async def test_customer_sees_only_own_orders(client: AsyncClient) -> None:
    admin = await _admin_headers(client)
    tenant = await client.post(
        "/api/v1/tenants",
        headers=admin,
        json={"name": "p25-scope", "slug": "p25-scope"},
    )
    tenant_id = tenant.json()["id"]
    admin["X-Tenant-ID"] = tenant_id

    cust_a = await _customer_headers(client, tenant_id, "cust-a@example.com")
    cust_b = await _customer_headers(client, tenant_id, "cust-b@example.com")

    biz = await client.post(
        "/api/v1/businesses",
        headers=admin,
        json={"name": "Kitchen", "type": "FOOD", "status": "ACTIVE"},
    )
    business_id = biz.json()["id"]
    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=admin,
        json={"name": "Burger"},
    )
    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product.json()['id']}/variants",
        headers=admin,
        json={"name": "Regular", "base_price_paise": 19900},
    )

    async def checkout(headers: dict[str, str]) -> str:
        cart = await client.post(
            "/api/v1/carts",
            headers=headers,
            json={"business_id": business_id, "delivery_fee_paise": 1000},
        )
        await client.post(
            f"/api/v1/carts/{cart.json()['id']}/items",
            headers=headers,
            json={"variant_id": variant.json()["id"], "quantity": 1},
        )
        order = await client.post(
            "/api/v1/orders/checkout",
            headers=headers,
            json={"cart_id": cart.json()["id"], "payment_provider": "cod"},
        )
        assert order.status_code == 200, order.text
        return order.json()["id"]

    order_a = await checkout(cust_a)
    order_b = await checkout(cust_b)

    list_a = await client.get("/api/v1/orders", headers=cust_a)
    assert list_a.status_code == 200
    ids_a = {o["id"] for o in list_a.json()}
    assert order_a in ids_a
    assert order_b not in ids_a

    peek_b = await client.get(f"/api/v1/orders/{order_b}", headers=cust_a)
    assert peek_b.status_code == 404

    cancel = await client.post(
        f"/api/v1/orders/{order_a}/transitions",
        headers=cust_a,
        json={"to_status": "CANCELLED", "actor": "customer"},
    )
    assert cancel.status_code == 200, cancel.text
    assert cancel.json()["status"] == "CANCELLED"
