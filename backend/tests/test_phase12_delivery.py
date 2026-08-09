"""Phase 12: delivery partners, vehicles, assignment V1, tracking."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.delivery.geo import haversine_km, in_service_area


def test_haversine_and_service_area() -> None:
    # ~1.1km between nearby Bengaluru points
    d = haversine_km(12.9352, 77.6245, 12.9452, 77.6245)
    assert 0.5 < d < 2.0
    assert in_service_area(
        partner_lat=12.9352,
        partner_lng=77.6245,
        pickup_lat=12.9452,
        pickup_lng=77.6245,
        service_area={"radius_km": 5},
    )
    assert not in_service_area(
        partner_lat=12.9352,
        partner_lng=77.6245,
        pickup_lat=13.5,
        pickup_lng=77.6245,
        service_area={"radius_km": 5, "center_lat": 12.9352, "center_lng": 77.6245},
    )


async def _admin_headers(client: AsyncClient) -> dict[str, str]:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _ready_order_with_location(client: AsyncClient, slug: str):
    headers = await _admin_headers(client)
    me = await client.get("/api/v1/auth/me", headers=headers)
    user_id = me.json()["id"]

    tenant = await client.post(
        "/api/v1/tenants", headers=headers, json={"name": slug, "slug": slug}
    )
    headers["X-Tenant-ID"] = tenant.json()["id"]
    biz = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={"name": "Kitchen", "type": "FOOD", "status": "ACTIVE"},
    )
    business_id = biz.json()["id"]
    loc = await client.post(
        f"/api/v1/businesses/{business_id}/locations",
        headers=headers,
        json={
            "name": "Store",
            "address": {
                "line1": "12 Main",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pincode": "560095",
            },
            "lat": 12.9352,
            "lng": 77.6245,
            "hours": [],
        },
    )
    assert loc.status_code == 200, loc.text
    location_id = loc.json()["id"]

    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=headers,
        json={"name": "Burger"},
    )
    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product.json()['id']}/variants",
        headers=headers,
        json={"name": "Regular", "base_price_paise": 19900},
    )
    cart = await client.post(
        "/api/v1/carts",
        headers=headers,
        json={
            "business_id": business_id,
            "location_id": location_id,
            "delivery_fee_paise": 3000,
            "platform_fee_paise": 500,
        },
    )
    await client.post(
        f"/api/v1/carts/{cart.json()['id']}/items",
        headers=headers,
        json={"variant_id": variant.json()["id"], "quantity": 1},
    )
    checkout = await client.post(
        "/api/v1/orders/checkout",
        headers=headers,
        json={"cart_id": cart.json()["id"], "payment_provider": "cod"},
    )
    assert checkout.status_code == 200, checkout.text
    order_id = checkout.json()["id"]

    for to_status, actor in (
        ("ACCEPTED", "merchant"),
        ("PREPARING", "merchant"),
        ("READY", "merchant"),
    ):
        resp = await client.post(
            f"/api/v1/orders/{order_id}/transitions",
            headers=headers,
            json={"to_status": to_status, "actor": actor},
        )
        assert resp.status_code == 200, resp.text

    ful = await client.get(f"/api/v1/orders/{order_id}/fulfillment", headers=headers)
    assert ful.status_code == 200
    assert ful.json()["status"] == "AWAITING_PICKUP"
    return headers, user_id, order_id, ful.json()["id"]


@pytest.mark.asyncio
async def test_assign_track_and_complete_delivery(client: AsyncClient) -> None:
    headers, user_id, order_id, fulfillment_id = await _ready_order_with_location(
        client, "del-happy"
    )

    partner = await client.post(
        "/api/v1/delivery-partners",
        headers=headers,
        json={
            "user_id": user_id,
            "display_name": "Rider One",
            "service_area": {"radius_km": 10, "center_lat": 12.9352, "center_lng": 77.6245},
        },
    )
    assert partner.status_code == 200, partner.text
    partner_id = partner.json()["id"]

    online = await client.post(
        f"/api/v1/delivery-partners/{partner_id}/location",
        headers=headers,
        json={"lat": 12.9360, "lng": 77.6250, "is_online": True},
    )
    assert online.status_code == 200
    assert online.json()["is_online"] is True

    vehicle = await client.post(
        "/api/v1/vehicles",
        headers=headers,
        json={"partner_id": partner_id, "vehicle_type": "BIKE", "registration": "KA01AB1234"},
    )
    assert vehicle.status_code == 200, vehicle.text

    delivery = await client.post(
        f"/api/v1/fulfillments/{fulfillment_id}/deliveries",
        headers=headers,
        json={"metadata": {"dropoff": {"lat": 12.9452, "lng": 77.6245}}},
    )
    if delivery.status_code == 409 or delivery.status_code == 400:
        delivery = await client.get(
            f"/api/v1/fulfillments/{fulfillment_id}/delivery",
            headers=headers,
        )
    assert delivery.status_code == 200, delivery.text
    body = delivery.json()
    assert body["status"] == "CREATED"
    assert len(body["stops"]) == 2
    assert body["stops"][0]["stop_type"] == "PICKUP"
    delivery_id = body["id"]

    ful = await client.get(f"/api/v1/orders/{order_id}/fulfillment", headers=headers)
    assert ful.json()["status"] == "AWAITING_PICKUP"

    assigned = await client.post(
        f"/api/v1/deliveries/{delivery_id}/assign", headers=headers, json={}
    )
    assert assigned.status_code == 200, assigned.text
    assert assigned.json()["status"] == "ASSIGNED"
    assert assigned.json()["partner_id"] == partner_id
    assert assigned.json()["vehicle_id"] == vehicle.json()["id"]
    assert assigned.json()["metadata"]["assignment"]["mode"] == "nearest_v1"

    tracked = await client.post(
        f"/api/v1/deliveries/{delivery_id}/tracking",
        headers=headers,
        json={"lat": 12.9370, "lng": 77.6255, "speed_kmh": 20},
    )
    assert tracked.status_code == 200
    assert tracked.json()["metadata"]["last_location"]["lat"] == 12.9370

    pickup = next(s for s in assigned.json()["stops"] if s["stop_type"] == "PICKUP")
    after_pickup = await client.post(
        f"/api/v1/deliveries/{delivery_id}/stops/{pickup['id']}/complete",
        headers=headers,
        json={"proof": {"otp": "1234"}},
    )
    assert after_pickup.status_code == 200, after_pickup.text
    assert after_pickup.json()["status"] == "EN_ROUTE_DROP"
    pickup_done = next(s for s in after_pickup.json()["stops"] if s["id"] == pickup["id"])
    assert pickup_done["status"] == "COMPLETED"
    assert pickup_done["proof"]["otp"] == "1234"

    drop = next(s for s in after_pickup.json()["stops"] if s["stop_type"] == "DROP")
    after_drop = await client.post(
        f"/api/v1/deliveries/{delivery_id}/stops/{drop['id']}/complete",
        headers=headers,
        json={"proof": {"photo_url": "https://cdn.example/pod.jpg"}},
    )
    assert after_drop.status_code == 200, after_drop.text
    assert after_drop.json()["status"] == "COMPLETED"

    ful2 = await client.get(f"/api/v1/orders/{order_id}/fulfillment", headers=headers)
    assert ful2.json()["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_no_partners_available(client: AsyncClient) -> None:
    headers, _user_id, _order_id, fulfillment_id = await _ready_order_with_location(
        client, "del-none"
    )
    delivery = await client.post(
        f"/api/v1/fulfillments/{fulfillment_id}/deliveries",
        headers=headers,
        json={},
    )
    if delivery.status_code != 200:
        delivery = await client.get(
            f"/api/v1/fulfillments/{fulfillment_id}/delivery",
            headers=headers,
        )
    assert delivery.status_code == 200
    assigned = await client.post(
        f"/api/v1/deliveries/{delivery.json()['id']}/assign",
        headers=headers,
        json={},
    )
    assert assigned.status_code == 409
    assert assigned.json()["error"]["code"] == "NO_PARTNERS_AVAILABLE"


@pytest.mark.asyncio
async def test_self_pickup_rejects_delivery(client: AsyncClient) -> None:
    headers = await _admin_headers(client)
    tenant = await client.post(
        "/api/v1/tenants",
        headers=headers,
        json={"name": "del-self", "slug": "del-self"},
    )
    headers["X-Tenant-ID"] = tenant.json()["id"]
    biz = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={"name": "Cafe", "type": "FOOD", "status": "ACTIVE"},
    )
    business_id = biz.json()["id"]
    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=headers,
        json={"name": "Tea"},
    )
    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product.json()['id']}/variants",
        headers=headers,
        json={"name": "Cup", "base_price_paise": 5000},
    )
    cart = await client.post(
        "/api/v1/carts",
        headers=headers,
        json={"business_id": business_id, "delivery_fee_paise": 0, "platform_fee_paise": 0},
    )
    await client.post(
        f"/api/v1/carts/{cart.json()['id']}/items",
        headers=headers,
        json={"variant_id": variant.json()["id"], "quantity": 1},
    )
    checkout = await client.post(
        "/api/v1/orders/checkout",
        headers=headers,
        json={
            "cart_id": cart.json()["id"],
            "payment_provider": "cod",
            "fulfillment_type": "SELF_PICKUP",
        },
    )
    ful = await client.get(
        f"/api/v1/orders/{checkout.json()['id']}/fulfillment", headers=headers
    )
    bad = await client.post(
        f"/api/v1/fulfillments/{ful.json()['id']}/deliveries",
        headers=headers,
        json={},
    )
    assert bad.status_code == 400
    assert bad.json()["error"]["code"] == "FULFILLMENT_NO_DELIVERY"
