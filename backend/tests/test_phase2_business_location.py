"""Phase 2: business onboarding and locations."""

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


@pytest.mark.asyncio
async def test_create_food_business_with_capabilities(client: AsyncClient) -> None:
    headers = await _tenant_setup(client, "p2-food")

    created = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={
            "name": "Spice Kitchen",
            "type": "FOOD",
            "status": "ACTIVE",
        },
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["type"] == "FOOD"
    assert body["capabilities"]["addons"] is True
    assert body["capabilities"]["inventory"] is False

    me = await client.get("/api/v1/auth/me", headers=headers)
    owner_bindings = [
        r for r in me.json()["roles"]
        if r["role"] == "BUSINESS_OWNER" and r["business_id"] == body["id"]
    ]
    assert len(owner_bindings) == 1


@pytest.mark.asyncio
async def test_grocery_business_gets_inventory_capability(client: AsyncClient) -> None:
    headers = await _tenant_setup(client, "p2-grocery")

    created = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={"name": "Fresh Mart", "type": "GROCERY", "status": "ACTIVE"},
    )
    assert created.status_code == 200, created.text
    assert created.json()["capabilities"]["inventory"] is True


@pytest.mark.asyncio
async def test_location_crud_under_business(client: AsyncClient) -> None:
    headers = await _tenant_setup(client, "p2-loc")

    biz = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={"name": "Corner Store", "type": "RETAIL", "status": "ACTIVE"},
    )
    business_id = biz.json()["id"]

    loc = await client.post(
        f"/api/v1/businesses/{business_id}/locations",
        headers=headers,
        json={
            "name": "Main Store",
            "address": {
                "line1": "12 MG Road",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pincode": "560001",
            },
            "lat": 12.9716,
            "lng": 77.5946,
            "hours": [{"day": "MON", "open": "09:00", "close": "21:00"}],
        },
    )
    assert loc.status_code == 200, loc.text
    location_id = loc.json()["id"]

    listed = await client.get(
        f"/api/v1/businesses/{business_id}/locations",
        headers=headers,
    )
    assert listed.status_code == 200, listed.text
    assert len(listed.json()) == 1

    updated = await client.patch(
        f"/api/v1/businesses/{business_id}/locations/{location_id}",
        headers=headers,
        json={"name": "MG Road Store"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["name"] == "MG Road Store"


@pytest.mark.asyncio
async def test_update_business_settings(client: AsyncClient) -> None:
    headers = await _tenant_setup(client, "p2-update")

    biz = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={"name": "Pause Test", "type": "FOOD", "status": "ACTIVE"},
    )
    business_id = biz.json()["id"]

    patched = await client.patch(
        f"/api/v1/businesses/{business_id}",
        headers=headers,
        json={
            "status": "PAUSED",
            "settings": {"preparation_time_minutes": 25},
        },
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["status"] == "PAUSED"
    assert patched.json()["settings"]["preparation_time_minutes"] == 25
