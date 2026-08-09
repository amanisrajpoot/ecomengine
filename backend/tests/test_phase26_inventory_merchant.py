"""Phase 26: merchant inventory UI API paths + locations.read for staff."""

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
    headers["X-Tenant-ID"] = tenant.json()["id"]
    biz = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={"name": f"{slug}-store", "type": "GROCERY", "status": "ACTIVE"},
    )
    business_id = biz.json()["id"]
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
    location_id = loc.json()["id"]
    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=headers,
        json={"name": "Milk 1L"},
    )
    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product.json()['id']}/variants",
        headers=headers,
        json={"name": "Default", "base_price_paise": 6000, "sku": "MILK-1L"},
    )
    return headers, business_id, location_id, variant.json()["id"]


@pytest.mark.asyncio
async def test_staff_can_list_locations_and_adjust_inventory(client: AsyncClient) -> None:
    admin, business_id, location_id, variant_id = await _grocery_setup(
        client, "p26-staff"
    )
    tenant_id = admin["X-Tenant-ID"]

    registered = await client.post(
        "/api/v1/auth/register",
        headers={"X-Tenant-ID": tenant_id},
        json={
            "email": "staff-p26@example.com",
            "password": "Staff123!",
            "display_name": "Staff",
        },
    )
    assert registered.status_code == 200, registered.text
    staff_user_id = registered.json()["user_id"]

    assign = await client.post(
        f"/api/v1/users/{staff_user_id}/roles",
        headers=admin,
        json={
            "role": "STAFF",
            "tenant_id": tenant_id,
            "business_id": business_id,
        },
    )
    assert assign.status_code == 200, assign.text

    staff = {
        "Authorization": f"Bearer {registered.json()['access_token']}",
        "X-Tenant-ID": tenant_id,
    }

    locations = await client.get(
        f"/api/v1/businesses/{business_id}/locations",
        headers=staff,
    )
    assert locations.status_code == 200, locations.text
    assert len(locations.json()) == 1

    item = await client.post(
        f"/api/v1/businesses/{business_id}/inventory",
        headers=staff,
        json={
            "location_id": location_id,
            "variant_id": variant_id,
            "low_stock_threshold": 3,
        },
    )
    assert item.status_code == 200, item.text
    item_id = item.json()["id"]

    adjusted = await client.post(
        f"/api/v1/businesses/{business_id}/inventory/{item_id}/adjust",
        headers=staff,
        json={"delta_on_hand": 2, "reason": "RECEIVE", "note": "Morning delivery"},
    )
    assert adjusted.status_code == 200, adjusted.text
    assert adjusted.json()["available"] == 2
    assert adjusted.json()["is_low_stock"] is True

    movements = await client.get(
        f"/api/v1/businesses/{business_id}/inventory/{item_id}/movements",
        headers=staff,
    )
    assert movements.status_code == 200
    assert any(m["reason"] == "RECEIVE" for m in movements.json())

    low = await client.get(
        f"/api/v1/businesses/{business_id}/inventory",
        headers=staff,
        params={"low_stock_only": True},
    )
    assert low.status_code == 200
    assert any(row["id"] == item_id for row in low.json())
