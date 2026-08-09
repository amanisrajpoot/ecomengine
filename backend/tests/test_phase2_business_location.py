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


async def _create_tenant(client: AsyncClient, slug: str) -> str:
    headers = await _admin_headers(client)
    resp = await client.post(
        "/api/v1/tenants",
        headers=headers,
        json={"name": slug, "slug": slug},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_create_food_business_with_default_capabilities(client: AsyncClient) -> None:
    tenant_id = await _create_tenant(client, "food-biz-tenant")
    headers = await _admin_headers(client)
    headers["X-Tenant-ID"] = tenant_id

    created = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={
            "name": "Spice Route",
            "type": "FOOD",
            "description": "North Indian",
            "contact": {"phone": "+919811111111"},
            "settings": {"preparation_time_minutes": 25},
            "status": "ACTIVE",
        },
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["type"] == "FOOD"
    assert body["capabilities"]["addons"] is True
    assert body["capabilities"]["inventory"] is False
    assert body["settings"]["preparation_time_minutes"] == 25
    assert body["status"] == "ACTIVE"

    listed = await client.get("/api/v1/businesses", headers=headers)
    assert listed.status_code == 200
    assert any(b["id"] == body["id"] for b in listed.json())


@pytest.mark.asyncio
async def test_grocery_capabilities_and_location_crud(client: AsyncClient) -> None:
    tenant_id = await _create_tenant(client, "grocery-biz-tenant")
    headers = await _admin_headers(client)
    headers["X-Tenant-ID"] = tenant_id

    biz = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={"name": "Fresh Mart", "type": "GROCERY", "status": "ACTIVE"},
    )
    assert biz.status_code == 200, biz.text
    assert biz.json()["capabilities"]["inventory"] is True
    business_id = biz.json()["id"]

    loc = await client.post(
        f"/api/v1/businesses/{business_id}/locations",
        headers=headers,
        json={
            "name": "Koramangala Store",
            "address": {
                "line1": "12 5th Block",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pincode": "560095",
            },
            "lat": 12.9352,
            "lng": 77.6245,
            "service_area": {"type": "radius", "radius_km": 5},
            "hours": [
                {"day": "mon", "open": "09:00", "close": "22:00"},
                {"day": "tue", "open": "09:00", "close": "22:00"},
            ],
            "timezone": "Asia/Kolkata",
        },
    )
    assert loc.status_code == 200, loc.text
    location = loc.json()
    assert location["address"]["pincode"] == "560095"
    assert location["service_area"]["radius_km"] == 5
    assert location["hours"][0]["day"] == "mon"

    location_id = location["id"]
    patched = await client.patch(
        f"/api/v1/businesses/{business_id}/locations/{location_id}",
        headers=headers,
        json={"is_active": False, "name": "Koramangala Store (temp closed)"},
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["is_active"] is False
    assert "temp closed" in patched.json()["name"]

    active_only = await client.get(
        f"/api/v1/businesses/{business_id}/locations",
        headers=headers,
        params={"active_only": True},
    )
    assert active_only.status_code == 200
    assert active_only.json() == []


@pytest.mark.asyncio
async def test_courier_type_and_capability_override(client: AsyncClient) -> None:
    tenant_id = await _create_tenant(client, "courier-biz-tenant")
    headers = await _admin_headers(client)
    headers["X-Tenant-ID"] = tenant_id

    created = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={
            "name": "City Dash",
            "type": "COURIER",
            "capabilities": {
                "catalog": False,
                "inventory": False,
                "addons": False,
                "delivery": True,
                "scheduledOrders": False,
            },
        },
    )
    assert created.status_code == 200, created.text
    caps = created.json()["capabilities"]
    assert caps["catalog"] is False
    assert caps["scheduledOrders"] is False
    assert caps["delivery"] is True


@pytest.mark.asyncio
async def test_business_requires_tenant_header(client: AsyncClient) -> None:
    headers = await _admin_headers(client)
    resp = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={"name": "No Tenant", "type": "RETAIL"},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "TENANT_REQUIRED"
