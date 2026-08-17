"""Phase 5: cart and pricing breakdown."""

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
    headers = {
        "Authorization": admin_headers["Authorization"],
        "X-Tenant-ID": tenant_id,
    }

    reg = await client.post(
        "/api/v1/auth/register",
        headers={"X-Tenant-ID": tenant_id},
        json={
            "email": f"{slug}@customer.example.com",
            "password": "CustomerPass123!",
            "display_name": "Test Customer",
        },
    )
    assert reg.status_code == 200, reg.text
    return {
        "Authorization": f"Bearer {reg.json()['access_token']}",
        "X-Tenant-ID": tenant_id,
    }


async def _food_menu(
    client: AsyncClient, tenant_id: str, slug: str
) -> tuple[str, str, str | None]:
    admin_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    admin_headers = {
        "Authorization": f"Bearer {admin_login.json()['access_token']}",
        "X-Tenant-ID": tenant_id,
    }

    biz = await client.post(
        "/api/v1/businesses",
        headers=admin_headers,
        json={"name": f"Kitchen {slug}", "type": "FOOD", "status": "ACTIVE"},
    )
    assert biz.status_code == 200, biz.text
    business_id = biz.json()["id"]

    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=admin_headers,
        json={"name": "Paneer Tikka"},
    )
    product_id = product.json()["id"]

    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product_id}/variants",
        headers=admin_headers,
        json={"name": "Full", "base_price_paise": 18000},
    )
    variant_id = variant.json()["id"]

    addon = await client.post(
        f"/api/v1/businesses/{business_id}/addons",
        headers=admin_headers,
        json={"name": "Extra Butter", "price_paise": 2000},
    )
    addon_id = addon.json()["id"] if addon.status_code == 200 else None

    return business_id, variant_id, addon_id


@pytest.mark.asyncio
async def test_cart_item_and_pricing_breakdown(client: AsyncClient) -> None:
    headers = await _tenant_and_customer(client, "p5-cart")
    business_id, variant_id, addon_id = await _food_menu(client, headers["X-Tenant-ID"], "p5")

    cart = await client.post(
        "/api/v1/carts",
        headers=headers,
        json={"business_id": business_id},
    )
    assert cart.status_code == 200, cart.text
    cart_id = cart.json()["id"]

    item_body: dict = {"variant_id": variant_id, "quantity": 2}
    if addon_id:
        item_body["addons"] = [{"addon_id": addon_id, "quantity": 1}]

    added = await client.post(
        f"/api/v1/carts/{cart_id}/items",
        headers=headers,
        json=item_body,
    )
    assert added.status_code == 200, added.text
    assert len(added.json()["items"]) == 1

    priced = await client.post(f"/api/v1/carts/{cart_id}/price", headers=headers)
    assert priced.status_code == 200, priced.text
    pricing = priced.json()["pricing"]
    assert pricing["subtotal_paise"] == 40000  # (18000+2000)*2
    assert pricing["delivery_fee_paise"] == 3000
    assert pricing["platform_fee_paise"] == 500
    assert pricing["total_paise"] == 43500
    assert pricing["subtotal_paise"] - pricing["discount_paise"] + pricing["delivery_fee_paise"] + pricing["platform_fee_paise"] + pricing["tax_paise"] == pricing["total_paise"]


@pytest.mark.asyncio
async def test_update_and_remove_cart_item(client: AsyncClient) -> None:
    headers = await _tenant_and_customer(client, "p5-update")
    business_id, variant_id, _ = await _food_menu(client, headers["X-Tenant-ID"], "p5u")

    cart = await client.post(
        "/api/v1/carts",
        headers=headers,
        json={"business_id": business_id},
    )
    cart_id = cart.json()["id"]

    item = await client.post(
        f"/api/v1/carts/{cart_id}/items",
        headers=headers,
        json={"variant_id": variant_id, "quantity": 1},
    )
    item_id = item.json()["items"][0]["id"]

    updated = await client.patch(
        f"/api/v1/carts/{cart_id}/items/{item_id}",
        headers=headers,
        json={"quantity": 3},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["items"][0]["quantity"] == 3

    removed = await client.delete(
        f"/api/v1/carts/{cart_id}/items/{item_id}",
        headers=headers,
    )
    assert removed.status_code == 200, removed.text
    assert len(removed.json()["items"]) == 0


@pytest.mark.asyncio
async def test_cart_forbidden_for_other_customer(client: AsyncClient) -> None:
    headers_a = await _tenant_and_customer(client, "p5-forbid")
    tenant_id = headers_a["X-Tenant-ID"]
    business_id, variant_id, _ = await _food_menu(client, tenant_id, "f")

    cart = await client.post(
        "/api/v1/carts",
        headers=headers_a,
        json={"business_id": business_id},
    )
    cart_id = cart.json()["id"]
    await client.post(
        f"/api/v1/carts/{cart_id}/items",
        headers=headers_a,
        json={"variant_id": variant_id, "quantity": 1},
    )

    reg_b = await client.post(
        "/api/v1/auth/register",
        headers={"X-Tenant-ID": tenant_id},
        json={
            "email": "other@customer.example.com",
            "password": "CustomerPass123!",
        },
    )
    headers_b = {
        "Authorization": f"Bearer {reg_b.json()['access_token']}",
        "X-Tenant-ID": tenant_id,
    }
    denied = await client.get(f"/api/v1/carts/{cart_id}", headers=headers_b)
    assert denied.status_code == 403, denied.text
