"""Phase 16: customer-facing catalog read + food discovery."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _admin_headers(client: AsyncClient) -> dict[str, str]:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.mark.asyncio
async def test_customer_can_browse_food_catalog(client: AsyncClient) -> None:
    admin = await _admin_headers(client)
    tenant = await client.post(
        "/api/v1/tenants",
        headers=admin,
        json={"name": "cust-pwa", "slug": "cust-pwa"},
    )
    tenant_id = tenant.json()["id"]
    admin["X-Tenant-ID"] = tenant_id

    biz = await client.post(
        "/api/v1/businesses",
        headers=admin,
        json={"name": "Dock Cafe", "type": "FOOD", "status": "ACTIVE"},
    )
    business_id = biz.json()["id"]
    loc = await client.post(
        f"/api/v1/businesses/{business_id}/locations",
        headers=admin,
        json={
            "name": "Dock",
            "address": {
                "line1": "1 Dock St",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pincode": "560001",
            },
            "lat": 12.9784,
            "lng": 77.6408,
            "service_area": {"type": "radius", "radius_km": 6},
        },
    )
    assert loc.status_code == 200, loc.text
    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=admin,
        json={"name": "Filter Coffee"},
    )
    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product.json()['id']}/variants",
        headers=admin,
        json={"name": "Regular", "base_price_paise": 8000},
    )
    assert variant.status_code == 200

    # Register a CUSTOMER in this tenant.
    registered = await client.post(
        "/api/v1/auth/register",
        headers={"X-Tenant-ID": tenant_id},
        json={
            "email": "customer-pwa@example.com",
            "password": "Customer123!",
            "display_name": "Cust",
        },
    )
    assert registered.status_code == 200, registered.text
    cust = {
        "Authorization": f"Bearer {registered.json()['access_token']}",
        "X-Tenant-ID": tenant_id,
    }

    nearby = await client.get(
        "/api/v1/stores/nearby",
        headers=cust,
        params={"lat": 12.979, "lng": 77.641, "radius_km": 5, "type": "FOOD"},
    )
    assert nearby.status_code == 200, nearby.text
    assert any(s["business_id"] == business_id for s in nearby.json())

    products = await client.get(
        f"/api/v1/businesses/{business_id}/products",
        headers=cust,
        params={"active_only": True},
    )
    assert products.status_code == 200, products.text
    assert products.json()[0]["name"] == "Filter Coffee"

    variants = await client.get(
        f"/api/v1/businesses/{business_id}/products/{product.json()['id']}/variants",
        headers=cust,
    )
    assert variants.status_code == 200
    assert variants.json()[0]["base_price_paise"] == 8000

    business = await client.get(f"/api/v1/businesses/{business_id}", headers=cust)
    assert business.status_code == 200
    assert business.json()["name"] == "Dock Cafe"
