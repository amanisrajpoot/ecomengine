"""Phase 30: ledger UI — merchant scoping and admin tenant-wide reads."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _admin_headers(client: AsyncClient) -> dict[str, str]:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _merchant_headers(
    client: AsyncClient, tenant_id: str, email: str, business_id: str
) -> dict[str, str]:
    registered = await client.post(
        "/api/v1/auth/register",
        headers={"X-Tenant-ID": tenant_id},
        json={"email": email, "password": "Merchant123!", "display_name": "Owner"},
    )
    assert registered.status_code == 200, registered.text
    user_id = registered.json()["user_id"]
    admin = await _admin_headers(client)
    admin["X-Tenant-ID"] = tenant_id
    assign = await client.post(
        f"/api/v1/users/{user_id}/roles",
        headers=admin,
        json={
            "role": "BUSINESS_OWNER",
            "tenant_id": tenant_id,
            "business_id": business_id,
        },
    )
    assert assign.status_code == 200, assign.text
    return {
        "Authorization": f"Bearer {registered.json()['access_token']}",
        "X-Tenant-ID": tenant_id,
    }


async def _checkout_on_business(
    client: AsyncClient, headers: dict[str, str], business_id: str
) -> str:
    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=headers,
        json={"name": "Meal"},
    )
    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product.json()['id']}/variants",
        headers=headers,
        json={"name": "Regular", "base_price_paise": 15000},
    )
    cart = await client.post(
        "/api/v1/carts",
        headers=headers,
        json={"business_id": business_id, "delivery_fee_paise": 3000},
    )
    await client.post(
        f"/api/v1/carts/{cart.json()['id']}/items",
        headers=headers,
        json={"variant_id": variant.json()["id"], "quantity": 1},
    )
    checkout = await client.post(
        "/api/v1/orders/checkout",
        headers=headers,
        json={"cart_id": cart.json()["id"], "payment_provider": "cod"},
    )
    assert checkout.status_code == 200, checkout.text
    return checkout.json()["id"]


@pytest.mark.asyncio
async def test_merchant_sees_only_own_business_ledger(client: AsyncClient) -> None:
    admin = await _admin_headers(client)
    tenant = await client.post(
        "/api/v1/tenants",
        headers=admin,
        json={"name": "p30-ledger", "slug": "p30-ledger"},
    )
    tenant_id = tenant.json()["id"]
    admin["X-Tenant-ID"] = tenant_id

    biz_a = (
        await client.post(
            "/api/v1/businesses",
            headers=admin,
            json={"name": "Kitchen A", "type": "FOOD", "status": "ACTIVE"},
        )
    ).json()["id"]
    biz_b = (
        await client.post(
            "/api/v1/businesses",
            headers=admin,
            json={"name": "Kitchen B", "type": "FOOD", "status": "ACTIVE"},
        )
    ).json()["id"]

    order_a = await _checkout_on_business(client, admin, biz_a)
    order_b = await _checkout_on_business(client, admin, biz_b)

    merchant_a = await _merchant_headers(client, tenant_id, "ledger-a@example.com", biz_a)
    merchant_b = await _merchant_headers(client, tenant_id, "ledger-b@example.com", biz_b)

    own = await client.get(
        f"/api/v1/orders/{order_a}/ledger",
        headers=merchant_a,
    )
    assert own.status_code == 200, own.text
    assert len(own.json()) >= 1

    peek = await client.get(
        f"/api/v1/orders/{order_b}/ledger",
        headers=merchant_a,
    )
    assert peek.status_code == 404

    scoped = await client.get(
        "/api/v1/ledger/entries",
        headers=merchant_a,
        params={"business_id": biz_a},
    )
    assert scoped.status_code == 200
    assert all(e["order_id"] == order_a for e in scoped.json())

    foreign = await client.get(
        "/api/v1/ledger/entries",
        headers=merchant_a,
        params={"business_id": biz_b},
    )
    assert foreign.status_code == 200
    assert foreign.json() == []


@pytest.mark.asyncio
async def test_admin_sees_tenant_wide_ledger(client: AsyncClient) -> None:
    admin = await _admin_headers(client)
    tenant = await client.post(
        "/api/v1/tenants",
        headers=admin,
        json={"name": "p30-admin-ledger", "slug": "p30-admin-ledger"},
    )
    tenant_id = tenant.json()["id"]
    admin["X-Tenant-ID"] = tenant_id

    biz = await client.post(
        "/api/v1/businesses",
        headers=admin,
        json={"name": "Ledger Cafe", "type": "FOOD", "status": "ACTIVE"},
    )
    assert biz.status_code == 200, biz.text
    order_id = await _checkout_on_business(client, admin, biz.json()["id"])

    ledger = await client.get(f"/api/v1/orders/{order_id}/ledger", headers=admin)
    assert ledger.status_code == 200, ledger.text
    assert any(e["account"] == "MERCHANT_PAYABLE" for e in ledger.json())

    balances = await client.get("/api/v1/ledger/balances", headers=admin)
    assert balances.status_code == 200
    assert any(b["account"] == "MERCHANT_PAYABLE" for b in balances.json())

    entries = await client.get("/api/v1/ledger/entries", headers=admin)
    assert entries.status_code == 200
    order_ids = {e["order_id"] for e in entries.json()}
    assert order_id in order_ids
