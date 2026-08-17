"""Phase 3: catalog — categories, products, variants, addons, bundles."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _admin_headers(client: AsyncClient) -> dict[str, str]:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _tenant_setup(client: AsyncClient, slug: str) -> dict[str, str]:
    headers = await _admin_headers(client)
    tenant = await client.post(
        "/api/v1/tenants",
        headers=headers,
        json={"name": slug, "slug": slug},
    )
    assert tenant.status_code == 200, tenant.text
    headers["X-Tenant-ID"] = tenant.json()["id"]
    return headers


async def _food_business(client: AsyncClient, headers: dict[str, str], name: str) -> str:
    biz = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={"name": name, "type": "FOOD", "status": "ACTIVE"},
    )
    assert biz.status_code == 200, biz.text
    return biz.json()["id"]


@pytest.mark.asyncio
async def test_category_and_product_with_variant(client: AsyncClient) -> None:
    headers = await _tenant_setup(client, "p3-catalog")
    business_id = await _food_business(client, headers, "Tandoor House")

    cat = await client.post(
        f"/api/v1/businesses/{business_id}/categories",
        headers=headers,
        json={"name": "Main", "sort_order": 1},
    )
    assert cat.status_code == 200, cat.text
    category_id = cat.json()["id"]

    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=headers,
        json={
            "name": "Butter Chicken",
            "category_id": category_id,
            "description": "Creamy tomato gravy",
            "tags": ["spicy"],
        },
    )
    assert product.status_code == 200, product.text
    product_id = product.json()["id"]

    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product_id}/variants",
        headers=headers,
        json={"name": "Regular", "base_price_paise": 24900},
    )
    assert variant.status_code == 200, variant.text
    assert variant.json()["base_price_paise"] == 24900

    listed = await client.get(
        f"/api/v1/businesses/{business_id}/products",
        headers=headers,
        params={"category_id": category_id},
    )
    assert listed.status_code == 200, listed.text
    assert len(listed.json()) == 1
    assert listed.json()[0]["name"] == "Butter Chicken"


@pytest.mark.asyncio
async def test_addon_link_and_bundle(client: AsyncClient) -> None:
    headers = await _tenant_setup(client, "p3-addons")
    business_id = await _food_business(client, headers, "Pizza Place")

    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=headers,
        json={"name": "Margherita"},
    )
    product_id = product.json()["id"]

    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product_id}/variants",
        headers=headers,
        json={"name": "Large", "base_price_paise": 39900},
    )
    variant_id = variant.json()["id"]

    addon = await client.post(
        f"/api/v1/businesses/{business_id}/addons",
        headers=headers,
        json={"name": "Extra Cheese", "price_paise": 5000, "max_qty": 2},
    )
    assert addon.status_code == 200, addon.text
    addon_id = addon.json()["id"]

    link = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product_id}/addon-links",
        headers=headers,
        json={
            "addon_id": addon_id,
            "group_name": "Toppings",
            "is_required": False,
        },
    )
    assert link.status_code == 200, link.text
    assert link.json()["group_name"] == "Toppings"

    bundle = await client.post(
        f"/api/v1/businesses/{business_id}/bundles",
        headers=headers,
        json={
            "name": "Family Combo",
            "price_paise": 79900,
            "items": [{"variant_id": variant_id, "quantity": 2}],
        },
    )
    assert bundle.status_code == 200, bundle.text
    assert bundle.json()["price_paise"] == 79900
    assert len(bundle.json()["items"]) == 1


@pytest.mark.asyncio
async def test_catalog_disabled_for_courier_business(client: AsyncClient) -> None:
    headers = await _tenant_setup(client, "p3-courier")

    biz = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={"name": "Quick Courier", "type": "COURIER", "status": "ACTIVE"},
    )
    assert biz.status_code == 200, biz.text
    business_id = biz.json()["id"]

    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=headers,
        json={"name": "Should Fail"},
    )
    assert product.status_code == 400, product.text
    assert product.json()["error"]["code"] == "CATALOG_NOT_ENABLED"


@pytest.mark.asyncio
async def test_addons_disabled_for_grocery(client: AsyncClient) -> None:
    headers = await _tenant_setup(client, "p3-grocery")

    biz = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={"name": "Daily Mart", "type": "GROCERY", "status": "ACTIVE"},
    )
    business_id = biz.json()["id"]

    addon = await client.post(
        f"/api/v1/businesses/{business_id}/addons",
        headers=headers,
        json={"name": "Extra Bag", "price_paise": 2000},
    )
    assert addon.status_code == 400, addon.text
    assert addon.json()["error"]["code"] == "ADDONS_NOT_ENABLED"
