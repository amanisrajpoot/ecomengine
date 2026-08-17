"""Phase 4: inventory and stock movements."""

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


async def _grocery_setup(client: AsyncClient, slug: str) -> tuple[dict[str, str], str, str, str]:
    """Return headers, business_id, location_id, variant_id for a grocery store."""
    headers = await _tenant_setup(client, slug)

    biz = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={"name": "Fresh Mart", "type": "GROCERY", "status": "ACTIVE"},
    )
    assert biz.status_code == 200, biz.text
    business_id = biz.json()["id"]

    loc = await client.post(
        f"/api/v1/businesses/{business_id}/locations",
        headers=headers,
        json={
            "name": "Store 1",
            "address": {
                "line1": "1 Market St",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pincode": "560001",
            },
            "lat": 12.97,
            "lng": 77.59,
        },
    )
    assert loc.status_code == 200, loc.text
    location_id = loc.json()["id"]

    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=headers,
        json={"name": "Rice 1kg"},
    )
    product_id = product.json()["id"]

    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product_id}/variants",
        headers=headers,
        json={"name": "Default", "base_price_paise": 12000, "sku": "RICE-1KG"},
    )
    assert variant.status_code == 200, variant.text
    variant_id = variant.json()["id"]

    return headers, business_id, location_id, variant_id


@pytest.mark.asyncio
async def test_create_inventory_and_adjust(client: AsyncClient) -> None:
    headers, business_id, location_id, variant_id = await _grocery_setup(client, "p4-inv")

    created = await client.post(
        f"/api/v1/businesses/{business_id}/locations/{location_id}/inventory-items",
        headers=headers,
        json={"variant_id": variant_id, "on_hand": 100, "low_stock_threshold": 10},
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["on_hand"] == 100
    assert body["available"] == 100
    inventory_item_id = body["id"]

    adjusted = await client.post(
        f"/api/v1/businesses/{business_id}/locations/{location_id}/inventory-items/{inventory_item_id}/adjust",
        headers=headers,
        json={"delta_on_hand": -5, "reason": "ADJUSTMENT"},
    )
    assert adjusted.status_code == 200, adjusted.text
    assert adjusted.json()["on_hand"] == 95

    movements = await client.get(
        f"/api/v1/businesses/{business_id}/locations/{location_id}/inventory-items/{inventory_item_id}/movements",
        headers=headers,
    )
    assert movements.status_code == 200, movements.text
    assert len(movements.json()) >= 2


@pytest.mark.asyncio
async def test_reserve_and_release_stock(client: AsyncClient) -> None:
    headers, business_id, location_id, variant_id = await _grocery_setup(client, "p4-reserve")

    item = await client.post(
        f"/api/v1/businesses/{business_id}/locations/{location_id}/inventory-items",
        headers=headers,
        json={"variant_id": variant_id, "on_hand": 50},
    )
    inventory_item_id = item.json()["id"]

    reserved = await client.post(
        f"/api/v1/businesses/{business_id}/locations/{location_id}/inventory-items/{inventory_item_id}/reserve",
        headers=headers,
        json={"quantity": 8},
    )
    assert reserved.status_code == 200, reserved.text
    assert reserved.json()["reserved"] == 8
    assert reserved.json()["available"] == 42

    released = await client.post(
        f"/api/v1/businesses/{business_id}/locations/{location_id}/inventory-items/{inventory_item_id}/release",
        headers=headers,
        json={"quantity": 3},
    )
    assert released.status_code == 200, released.text
    assert released.json()["reserved"] == 5
    assert released.json()["available"] == 45


@pytest.mark.asyncio
async def test_low_stock_listing(client: AsyncClient) -> None:
    headers, business_id, location_id, variant_id = await _grocery_setup(client, "p4-low")

    item = await client.post(
        f"/api/v1/businesses/{business_id}/locations/{location_id}/inventory-items",
        headers=headers,
        json={"variant_id": variant_id, "on_hand": 8, "low_stock_threshold": 10},
    )
    inventory_item_id = item.json()["id"]

    low = await client.get(
        f"/api/v1/businesses/{business_id}/inventory/low-stock",
        headers=headers,
    )
    assert low.status_code == 200, low.text
    assert any(row["id"] == inventory_item_id for row in low.json())


@pytest.mark.asyncio
async def test_inventory_disabled_for_food_business(client: AsyncClient) -> None:
    headers = await _tenant_setup(client, "p4-food")

    biz = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={"name": "Spice Kitchen", "type": "FOOD", "status": "ACTIVE"},
    )
    business_id = biz.json()["id"]

    loc = await client.post(
        f"/api/v1/businesses/{business_id}/locations",
        headers=headers,
        json={
            "name": "Kitchen",
            "address": {
                "line1": "2 Food Lane",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pincode": "560001",
            },
            "lat": 12.97,
            "lng": 77.59,
        },
    )
    location_id = loc.json()["id"]

    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=headers,
        json={"name": "Curry"},
    )
    product_id = product.json()["id"]

    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product_id}/variants",
        headers=headers,
        json={"name": "Regular", "base_price_paise": 15000},
    )
    variant_id = variant.json()["id"]

    created = await client.post(
        f"/api/v1/businesses/{business_id}/locations/{location_id}/inventory-items",
        headers=headers,
        json={"variant_id": variant_id, "on_hand": 10},
    )
    assert created.status_code == 400, created.text
    assert created.json()["error"]["code"] == "INVENTORY_NOT_ENABLED"
