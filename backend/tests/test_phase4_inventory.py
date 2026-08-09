"""Phase 4: optional inventory with movement-backed stock mutations."""

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


async def _grocery_setup(client: AsyncClient, slug: str) -> tuple[dict[str, str], str, str, str]:
    headers = await _admin_headers(client)
    tenant = await client.post(
        "/api/v1/tenants", headers=headers, json={"name": slug, "slug": slug}
    )
    assert tenant.status_code == 200, tenant.text
    headers["X-Tenant-ID"] = tenant.json()["id"]

    biz = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={"name": f"{slug}-store", "type": "GROCERY", "status": "ACTIVE"},
    )
    assert biz.status_code == 200, biz.text
    business_id = biz.json()["id"]
    assert biz.json()["capabilities"]["inventory"] is True

    loc = await client.post(
        f"/api/v1/businesses/{business_id}/locations",
        headers=headers,
        json={
            "name": "Main",
            "address": {
                "line1": "1 MG Road",
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
        json={"name": "Milk 1L"},
    )
    assert product.status_code == 200, product.text
    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product.json()['id']}/variants",
        headers=headers,
        json={"name": "Default", "base_price_paise": 6000, "sku": "MILK-1L"},
    )
    assert variant.status_code == 200, variant.text
    return headers, business_id, location_id, variant.json()["id"]


@pytest.mark.asyncio
async def test_receive_reserve_consume_flow(client: AsyncClient) -> None:
    headers, business_id, location_id, variant_id = await _grocery_setup(
        client, "inv-flow"
    )

    item = await client.post(
        f"/api/v1/businesses/{business_id}/inventory",
        headers=headers,
        json={
            "location_id": location_id,
            "variant_id": variant_id,
            "low_stock_threshold": 5,
        },
    )
    assert item.status_code == 200, item.text
    item_id = item.json()["id"]
    assert item.json()["available"] == 0
    assert item.json()["is_out_of_stock"] is True

    received = await client.post(
        f"/api/v1/businesses/{business_id}/inventory/{item_id}/adjust",
        headers=headers,
        json={"delta_on_hand": 20, "reason": "RECEIVE", "note": "PO-1"},
    )
    assert received.status_code == 200, received.text
    assert received.json()["on_hand"] == 20
    assert received.json()["available"] == 20

    reserved = await client.post(
        f"/api/v1/businesses/{business_id}/inventory/{item_id}/reserve",
        headers=headers,
        json={"quantity": 3},
    )
    assert reserved.status_code == 200, reserved.text
    assert reserved.json()["reserved"] == 3
    assert reserved.json()["available"] == 17

    consumed = await client.post(
        f"/api/v1/businesses/{business_id}/inventory/{item_id}/consume",
        headers=headers,
        json={"quantity": 3},
    )
    assert consumed.status_code == 200, consumed.text
    assert consumed.json()["on_hand"] == 17
    assert consumed.json()["reserved"] == 0
    assert consumed.json()["available"] == 17

    movements = await client.get(
        f"/api/v1/businesses/{business_id}/inventory/{item_id}/movements",
        headers=headers,
    )
    assert movements.status_code == 200
    reasons = {m["reason"] for m in movements.json()}
    assert reasons == {"RECEIVE", "RESERVE", "CONSUME"}


@pytest.mark.asyncio
async def test_insufficient_stock_and_release(client: AsyncClient) -> None:
    headers, business_id, location_id, variant_id = await _grocery_setup(
        client, "inv-insufficient"
    )
    item = await client.post(
        f"/api/v1/businesses/{business_id}/inventory",
        headers=headers,
        json={"location_id": location_id, "variant_id": variant_id, "low_stock_threshold": 2},
    )
    item_id = item.json()["id"]
    await client.post(
        f"/api/v1/businesses/{business_id}/inventory/{item_id}/adjust",
        headers=headers,
        json={"delta_on_hand": 4, "reason": "RECEIVE"},
    )
    await client.post(
        f"/api/v1/businesses/{business_id}/inventory/{item_id}/reserve",
        headers=headers,
        json={"quantity": 3},
    )
    fail = await client.post(
        f"/api/v1/businesses/{business_id}/inventory/{item_id}/reserve",
        headers=headers,
        json={"quantity": 2},
    )
    assert fail.status_code == 409
    assert fail.json()["error"]["code"] == "INSUFFICIENT_STOCK"

    released = await client.post(
        f"/api/v1/businesses/{business_id}/inventory/{item_id}/release",
        headers=headers,
        json={"quantity": 3},
    )
    assert released.status_code == 200
    assert released.json()["available"] == 4

    low = await client.get(
        f"/api/v1/businesses/{business_id}/inventory",
        headers=headers,
        params={"low_stock_only": True},
    )
    # threshold 2, available 4 -> not low
    assert low.json() == []

    await client.post(
        f"/api/v1/businesses/{business_id}/inventory/{item_id}/adjust",
        headers=headers,
        json={"delta_on_hand": -3, "reason": "ADJUSTMENT"},
    )
    low2 = await client.get(
        f"/api/v1/businesses/{business_id}/inventory",
        headers=headers,
        params={"low_stock_only": True},
    )
    assert len(low2.json()) == 1
    assert low2.json()[0]["is_low_stock"] is True


@pytest.mark.asyncio
async def test_food_inventory_disabled(client: AsyncClient) -> None:
    headers = await _admin_headers(client)
    tenant = await client.post(
        "/api/v1/tenants",
        headers=headers,
        json={"name": "inv-food", "slug": "inv-food"},
    )
    headers["X-Tenant-ID"] = tenant.json()["id"]
    biz = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={"name": "Cafe", "type": "FOOD", "status": "ACTIVE"},
    )
    business_id = biz.json()["id"]
    assert biz.json()["capabilities"]["inventory"] is False

    loc = await client.post(
        f"/api/v1/businesses/{business_id}/locations",
        headers=headers,
        json={
            "name": "Kitchen",
            "address": {
                "line1": "2 Food St",
                "city": "Mumbai",
                "state": "Maharashtra",
                "pincode": "400001",
            },
            "lat": 19.07,
            "lng": 72.87,
        },
    )
    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=headers,
        json={"name": "Idli"},
    )
    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product.json()['id']}/variants",
        headers=headers,
        json={"name": "Plate", "base_price_paise": 4000},
    )
    resp = await client.post(
        f"/api/v1/businesses/{business_id}/inventory",
        headers=headers,
        json={
            "location_id": loc.json()["id"],
            "variant_id": variant.json()["id"],
        },
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "INVENTORY_DISABLED"
