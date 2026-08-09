"""Phase 3: generic catalog engine."""

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


async def _tenant_and_business(
    client: AsyncClient, *, slug: str, business_type: str = "FOOD"
) -> tuple[dict[str, str], str]:
    headers = await _admin_headers(client)
    tenant = await client.post(
        "/api/v1/tenants",
        headers=headers,
        json={"name": slug, "slug": slug},
    )
    assert tenant.status_code == 200, tenant.text
    tenant_id = tenant.json()["id"]
    headers["X-Tenant-ID"] = tenant_id
    biz = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={"name": f"{slug}-biz", "type": business_type, "status": "ACTIVE"},
    )
    assert biz.status_code == 200, biz.text
    return headers, biz.json()["id"]


@pytest.mark.asyncio
async def test_food_menu_category_product_variants_addons(client: AsyncClient) -> None:
    headers, business_id = await _tenant_and_business(client, slug="catalog-food")

    cat = await client.post(
        f"/api/v1/businesses/{business_id}/categories",
        headers=headers,
        json={"name": "Burgers", "sort_order": 1},
    )
    assert cat.status_code == 200, cat.text
    category_id = cat.json()["id"]

    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=headers,
        json={
            "name": "Classic Burger",
            "category_id": category_id,
            "description": "Beef patty",
            "images": ["s3://menu/burger.jpg"],
            "tags": ["bestseller"],
        },
    )
    assert product.status_code == 200, product.text
    product_id = product.json()["id"]

    regular = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product_id}/variants",
        headers=headers,
        json={"name": "Regular", "base_price_paise": 19900, "sku": "BRG-REG"},
    )
    large = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product_id}/variants",
        headers=headers,
        json={"name": "Large", "base_price_paise": 24900, "sku": "BRG-LRG"},
    )
    assert regular.status_code == 200, regular.text
    assert large.status_code == 200, large.text
    assert large.json()["base_price_paise"] == 24900
    assert "metadata" in large.json()

    cheese = await client.post(
        f"/api/v1/businesses/{business_id}/addons",
        headers=headers,
        json={"name": "Cheese", "price_paise": 3000, "max_qty": 2},
    )
    assert cheese.status_code == 200, cheese.text
    link = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product_id}/addons",
        headers=headers,
        json={"addon_id": cheese.json()["id"], "group_name": "extras", "is_required": False},
    )
    assert link.status_code == 200, link.text

    variants = await client.get(
        f"/api/v1/businesses/{business_id}/products/{product_id}/variants",
        headers=headers,
    )
    assert len(variants.json()) == 2

    bundle = await client.post(
        f"/api/v1/businesses/{business_id}/bundles",
        headers=headers,
        json={
            "name": "Burger Combo",
            "price_paise": 29900,
            "items": [{"variant_id": regular.json()["id"], "quantity": 1}],
        },
    )
    assert bundle.status_code == 200, bundle.text
    assert bundle.json()["items"][0]["variant_id"] == regular.json()["id"]


@pytest.mark.asyncio
async def test_retail_variants_without_addons_capability(client: AsyncClient) -> None:
    headers, business_id = await _tenant_and_business(
        client, slug="catalog-retail", business_type="RETAIL"
    )

    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=headers,
        json={"name": "T-Shirt"},
    )
    assert product.status_code == 200, product.text
    product_id = product.json()["id"]

    for size, price in [("Small", 49900), ("Medium", 49900), ("Large", 54900)]:
        resp = await client.post(
            f"/api/v1/businesses/{business_id}/products/{product_id}/variants",
            headers=headers,
            json={"name": size, "base_price_paise": price},
        )
        assert resp.status_code == 200, resp.text

    addon = await client.post(
        f"/api/v1/businesses/{business_id}/addons",
        headers=headers,
        json={"name": "Gift Wrap", "price_paise": 5000},
    )
    assert addon.status_code == 409
    assert addon.json()["error"]["code"] == "ADDONS_DISABLED"


@pytest.mark.asyncio
async def test_courier_catalog_disabled(client: AsyncClient) -> None:
    headers, business_id = await _tenant_and_business(
        client, slug="catalog-courier", business_type="COURIER"
    )
    resp = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=headers,
        json={"name": "Should Fail"},
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "CATALOG_DISABLED"


@pytest.mark.asyncio
async def test_update_product_availability(client: AsyncClient) -> None:
    headers, business_id = await _tenant_and_business(client, slug="catalog-avail")
    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=headers,
        json={"name": "Pasta"},
    )
    product_id = product.json()["id"]
    patched = await client.patch(
        f"/api/v1/businesses/{business_id}/products/{product_id}",
        headers=headers,
        json={"is_active": False},
    )
    assert patched.status_code == 200
    assert patched.json()["is_active"] is False

    active = await client.get(
        f"/api/v1/businesses/{business_id}/products",
        headers=headers,
        params={"active_only": True},
    )
    assert active.json() == []
