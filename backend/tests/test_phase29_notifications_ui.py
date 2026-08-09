"""Phase 29: notifications UI — customer scoping and admin tenant-wide list."""

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
    client: AsyncClient, cust: dict[str, str], setup: dict[str, str], phone: str
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
    checkout = await client.post(
        "/api/v1/orders/checkout",
        headers=cust,
        json={
            "cart_id": cart.json()["id"],
            "payment_provider": "cod",
            "customer_phone": phone,
        },
    )
    assert checkout.status_code == 200, checkout.text
    return checkout.json()["id"]


@pytest.mark.asyncio
async def test_customer_sees_only_own_notifications(client: AsyncClient) -> None:
    admin = await _admin_headers(client)
    setup = await _setup_tenant(client, admin, "p29-notify")
    tenant_id = setup["X-Tenant-ID"]

    cust_a = await _customer_headers(client, tenant_id, "notify-a@example.com")
    cust_b = await _customer_headers(client, tenant_id, "notify-b@example.com")

    order_a = await _customer_cart(client, cust_a, setup, "9876500001")
    order_b = await _customer_cart(client, cust_b, setup, "9876500002")

    notes_a = await client.get(
        "/api/v1/notifications",
        headers=cust_a,
        params={"order_id": order_a},
    )
    assert notes_a.status_code == 200, notes_a.text
    assert len(notes_a.json()) >= 1
    assert all(n["order_id"] == order_a for n in notes_a.json())

    peek_b = await client.get(
        "/api/v1/notifications",
        headers=cust_a,
        params={"order_id": order_b},
    )
    assert peek_b.status_code == 200
    assert peek_b.json() == []


@pytest.mark.asyncio
async def test_admin_sees_tenant_wide_notifications(client: AsyncClient) -> None:
    admin = await _admin_headers(client)
    setup = await _setup_tenant(client, admin, "p29-admin-notify")
    tenant_id = setup["X-Tenant-ID"]

    cust = await _customer_headers(client, tenant_id, "notify-admin@example.com")
    order_id = await _customer_cart(client, cust, setup, "9876500099")

    notes = await client.get(
        "/api/v1/notifications",
        headers=setup,
        params={"order_id": order_id},
    )
    assert notes.status_code == 200, notes.text
    rows = notes.json()
    assert len(rows) >= 1
    assert all(n["recipient"] == "9876500099" for n in rows)

    all_notes = await client.get("/api/v1/notifications", headers=setup, params={"limit": 200})
    assert all_notes.status_code == 200
    order_ids = {n["order_id"] for n in all_notes.json()}
    assert order_id in order_ids
