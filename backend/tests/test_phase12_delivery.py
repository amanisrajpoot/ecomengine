"""Phase 12: delivery partners, assignment V1, stops."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

PICKUP = {"line1": "12 Kitchen St", "city": "Bengaluru", "state": "KA", "pincode": "560001"}
DROP = {"line1": "88 Home Ave", "city": "Bengaluru", "state": "KA", "pincode": "560002"}


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
        json={"email": f"{slug}-rider@example.com", "password": "RiderPass123!"},
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


async def _checkout_with_fulfillment(
    client: AsyncClient, headers: dict[str, str], slug: str
) -> tuple[str, str]:
    admin = await _admin_headers(client, headers["X-Tenant-ID"])
    biz = await client.post(
        "/api/v1/businesses",
        headers=admin,
        json={"name": f"Del {slug}", "type": "FOOD", "status": "ACTIVE"},
    )
    business_id = biz.json()["id"]
    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=admin,
        json={"name": "Biryani"},
    )
    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product.json()['id']}/variants",
        headers=admin,
        json={"name": "Full", "base_price_paise": 22000},
    )
    cart = await client.post(
        "/api/v1/carts",
        headers=headers,
        json={"business_id": business_id},
    )
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
    assert order.status_code == 200, order.text
    order_id = order.json()["id"]
    fulfillment = await client.get(f"/api/v1/orders/{order_id}/fulfillment", headers=admin)
    return fulfillment.json()["id"], business_id


@pytest.mark.asyncio
async def test_delivery_auto_assign_nearest_partner(client: AsyncClient) -> None:
    headers = await _tenant_and_customer(client, "p12-assign")
    tenant_id = headers["X-Tenant-ID"]
    admin = await _admin_headers(client, tenant_id)
    fulfillment_id, _ = await _checkout_with_fulfillment(client, headers, "assign")

    far_rider = await _register_rider(client, tenant_id, "p12-far")
    await client.post("/api/v1/partners/profiles", headers=far_rider, json={})
    await client.patch(
        "/api/v1/partners/profiles/me",
        headers=far_rider,
        json={"is_online": True, "current_lat": 13.0, "current_lng": 77.6},
    )

    near_rider = await _register_rider(client, tenant_id, "p12-near")
    near_profile = await client.post("/api/v1/partners/profiles", headers=near_rider, json={})
    near_partner_id = near_profile.json()["id"]
    await client.patch(
        "/api/v1/partners/profiles/me",
        headers=near_rider,
        json={"is_online": True, "current_lat": 12.9716, "current_lng": 77.5946},
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
                    "address": PICKUP,
                    "lat": 12.9716,
                    "lng": 77.5946,
                    "contact": {"name": "Kitchen"},
                },
                {
                    "sequence": 1,
                    "stop_type": "DROP",
                    "address": DROP,
                    "lat": 12.975,
                    "lng": 77.6,
                    "contact": {"name": "Customer"},
                },
            ],
        },
    )
    assert delivery.status_code == 200, delivery.text
    body = delivery.json()
    assert body["status"] == "ASSIGNED"
    assert body["partner_id"] == near_partner_id
    assert len(body["stops"]) == 2


@pytest.mark.asyncio
async def test_complete_stops_finishes_delivery(client: AsyncClient) -> None:
    headers = await _tenant_and_customer(client, "p12-complete")
    tenant_id = headers["X-Tenant-ID"]
    admin = await _admin_headers(client, tenant_id)
    rider = await _register_rider(client, tenant_id, "p12-rider")
    await client.post("/api/v1/partners/profiles", headers=rider, json={})
    await client.patch(
        "/api/v1/partners/profiles/me",
        headers=rider,
        json={"is_online": True, "current_lat": 12.97, "current_lng": 77.59},
    )

    fulfillment_id, _ = await _checkout_with_fulfillment(client, headers, "complete")
    created = await client.post(
        f"/api/v1/fulfillments/{fulfillment_id}/deliveries",
        headers=admin,
        json={
            "auto_assign": True,
            "stops": [
                {
                    "sequence": 0,
                    "stop_type": "PICKUP",
                    "address": PICKUP,
                    "lat": 12.97,
                    "lng": 77.59,
                },
                {
                    "sequence": 1,
                    "stop_type": "DROP",
                    "address": DROP,
                    "lat": 12.98,
                    "lng": 77.61,
                },
            ],
        },
    )
    delivery_id = created.json()["id"]
    stops = created.json()["stops"]
    pickup_id = next(s["id"] for s in stops if s["stop_type"] == "PICKUP")
    drop_id = next(s["id"] for s in stops if s["stop_type"] == "DROP")

    after_pickup = await client.post(
        f"/api/v1/deliveries/{delivery_id}/stops/{pickup_id}/complete",
        headers=rider,
        json={"proof": {"type": "OTP", "code": "1234"}},
    )
    assert after_pickup.status_code == 200, after_pickup.text
    assert after_pickup.json()["status"] == "IN_PROGRESS"

    after_drop = await client.post(
        f"/api/v1/deliveries/{delivery_id}/stops/{drop_id}/complete",
        headers=rider,
        json={"proof": {"type": "PHOTO", "url": "s3://proof.jpg"}},
    )
    assert after_drop.status_code == 200, after_drop.text
    assert after_drop.json()["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_partner_vehicle_registration(client: AsyncClient) -> None:
    headers = await _tenant_and_customer(client, "p12-vehicle")
    tenant_id = headers["X-Tenant-ID"]
    rider = await _register_rider(client, tenant_id, "p12-v")
    await client.post("/api/v1/partners/profiles", headers=rider, json={})

    vehicle = await client.post(
        "/api/v1/partners/vehicles",
        headers=rider,
        json={"vehicle_type": "BIKE", "registration": "KA01AB1234"},
    )
    assert vehicle.status_code == 200, vehicle.text
    assert vehicle.json()["vehicle_type"] == "BIKE"

    listed = await client.get("/api/v1/partners/vehicles", headers=rider)
    assert listed.status_code == 200
    assert len(listed.json()) == 1


@pytest.mark.asyncio
async def test_list_my_deliveries(client: AsyncClient) -> None:
    headers = await _tenant_and_customer(client, "p12-my-deliveries")
    tenant_id = headers["X-Tenant-ID"]
    admin = await _admin_headers(client, tenant_id)
    rider = await _register_rider(client, tenant_id, "p12-my")
    await client.post("/api/v1/partners/profiles", headers=rider, json={})
    await client.patch(
        "/api/v1/partners/profiles/me",
        headers=rider,
        json={"is_online": True, "current_lat": 12.97, "current_lng": 77.59},
    )

    fulfillment_id, _ = await _checkout_with_fulfillment(client, headers, "my-del")
    await client.post(
        f"/api/v1/fulfillments/{fulfillment_id}/deliveries",
        headers=admin,
        json={
            "auto_assign": True,
            "stops": [
                {
                    "sequence": 0,
                    "stop_type": "PICKUP",
                    "address": PICKUP,
                    "lat": 12.97,
                    "lng": 77.59,
                },
                {
                    "sequence": 1,
                    "stop_type": "DROP",
                    "address": DROP,
                    "lat": 12.98,
                    "lng": 77.61,
                },
            ],
        },
    )

    mine = await client.get("/api/v1/deliveries/me", headers=rider)
    assert mine.status_code == 200, mine.text
    assert len(mine.json()) == 1
    assert mine.json()[0]["status"] == "ASSIGNED"
