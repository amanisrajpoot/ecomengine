"""Phase 24: Order tracking projection and partner GPS ping."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

PICKUP_LAT, PICKUP_LNG = 12.9716, 77.5946
DROP_LAT, DROP_LNG = 12.9750, 77.6000
RIDER_LAT, RIDER_LNG = 12.9720, 77.5950


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
    reg = await client.post(
        "/api/v1/auth/register",
        headers={"X-Tenant-ID": tenant_id},
        json={"email": f"{slug}@customer.example.com", "password": "CustomerPass123!"},
    )
    return {
        "Authorization": f"Bearer {reg.json()['access_token']}",
        "X-Tenant-ID": tenant_id,
    }


async def _admin_headers(client: AsyncClient, tenant_id: str) -> dict[str, str]:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    return {
        "Authorization": f"Bearer {login.json()['access_token']}",
        "X-Tenant-ID": tenant_id,
    }


async def _register_rider(client: AsyncClient, tenant_id: str, slug: str) -> dict[str, str]:
    reg = await client.post(
        "/api/v1/auth/register",
        headers={"X-Tenant-ID": tenant_id},
        json={"email": f"{slug}-rider@track.example.com", "password": "RiderPass123!"},
    )
    rider_headers = {
        "Authorization": f"Bearer {reg.json()['access_token']}",
        "X-Tenant-ID": tenant_id,
    }
    admin = await _admin_headers(client, tenant_id)
    await client.post(
        f"/api/v1/users/{reg.json()['user_id']}/roles",
        headers=admin,
        json={"role": "DELIVERY_PARTNER", "tenant_id": tenant_id},
    )
    return rider_headers


@pytest.mark.asyncio
async def test_order_tracking_and_partner_location(client: AsyncClient) -> None:
    headers = await _tenant_and_customer(client, "p24-track")
    tenant_id = headers["X-Tenant-ID"]
    admin = await _admin_headers(client, tenant_id)

    biz = await client.post(
        "/api/v1/businesses",
        headers=admin,
        json={"name": "Track Kitchen", "type": "FOOD", "status": "ACTIVE"},
    )
    business_id = biz.json()["id"]

    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=admin,
        json={"name": "Meal"},
    )
    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product.json()['id']}/variants",
        headers=admin,
        json={"name": "Regular", "base_price_paise": 15000},
    )

    cart = await client.post("/api/v1/carts", headers=headers, json={"business_id": business_id})
    cart_id = cart.json()["id"]
    await client.post(
        f"/api/v1/carts/{cart_id}/items",
        headers=headers,
        json={"variant_id": variant.json()["id"], "quantity": 1},
    )

    order = await client.post(
        "/api/v1/orders/checkout",
        headers=headers,
        json={"cart_id": cart_id, "fulfillment_type": "DELIVERY"},
    )
    order_id = order.json()["id"]
    fulfillment_id = (
        await client.get(f"/api/v1/orders/{order_id}/fulfillment", headers=headers)
    ).json()["id"]

    rider = await _register_rider(client, tenant_id, "p24")
    await client.post("/api/v1/partners/profiles", headers=rider, json={})
    await client.patch(
        "/api/v1/partners/profiles/me",
        headers=rider,
        json={"is_online": True, "current_lat": PICKUP_LAT, "current_lng": PICKUP_LNG},
    )

    delivery = await client.post(
        f"/api/v1/fulfillments/{fulfillment_id}/deliveries",
        headers=admin,
        json={
            "auto_assign": True,
            "stops": [
                {
                    "sequence": 0,
                    "stop_type": "PICKUP",
                    "address": {"line1": "Kitchen", "city": "Bengaluru", "pincode": "560001"},
                    "lat": PICKUP_LAT,
                    "lng": PICKUP_LNG,
                    "contact": {"name": "Kitchen"},
                },
                {
                    "sequence": 1,
                    "stop_type": "DROP",
                    "address": {"line1": "Customer", "city": "Bengaluru", "pincode": "560034"},
                    "lat": DROP_LAT,
                    "lng": DROP_LNG,
                    "contact": {"name": "Customer"},
                },
            ],
        },
    )
    assert delivery.status_code == 200, delivery.text
    delivery_id = delivery.json()["id"]

    location_ping = await client.post(
        "/api/v1/partners/profiles/me/location",
        headers=rider,
        json={"lat": RIDER_LAT, "lng": RIDER_LNG},
    )
    assert location_ping.status_code == 200, location_ping.text
    assert location_ping.json()["current_lat"] == RIDER_LAT
    assert location_ping.json()["current_lng"] == RIDER_LNG

    tracking = await client.get(f"/api/v1/orders/{order_id}/tracking", headers=headers)
    assert tracking.status_code == 200, tracking.text
    body = tracking.json()
    assert body["order_id"] == order_id
    assert body["delivery_id"] == delivery_id
    assert len(body["stops"]) == 2
    assert body["rider"] is not None
    assert body["rider"]["lat"] == RIDER_LAT
    assert body["rider"]["lng"] == RIDER_LNG

    pickup = next(s for s in body["stops"] if s["stop_type"] == "PICKUP")
    drop = next(s for s in body["stops"] if s["stop_type"] == "DROP")
    assert pickup["lat"] == PICKUP_LAT
    assert drop["lat"] == DROP_LAT
