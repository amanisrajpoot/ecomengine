"""Phase 18: rider delivery list, location, and POD completion."""

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
async def test_rider_lists_and_completes_assigned_delivery(client: AsyncClient) -> None:
    headers = await _admin_headers(client)
    me = await client.get("/api/v1/auth/me", headers=headers)
    user_id = me.json()["id"]

    tenant = await client.post(
        "/api/v1/tenants",
        headers=headers,
        json={"name": "rider-pwa", "slug": "rider-pwa"},
    )
    tenant_id = tenant.json()["id"]
    headers["X-Tenant-ID"] = tenant_id

    biz = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={"name": "Rider Kitchen", "type": "FOOD", "status": "ACTIVE"},
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
        },
    )
    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=headers,
        json={"name": "Meal"},
    )
    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product.json()['id']}/variants",
        headers=headers,
        json={"name": "Box", "base_price_paise": 12000},
    )
    cart = await client.post(
        "/api/v1/carts",
        headers=headers,
        json={"business_id": business_id, "location_id": loc.json()["id"]},
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
    order_id = checkout.json()["id"]
    for to_status, actor in (
        ("ACCEPTED", "merchant"),
        ("PREPARING", "merchant"),
        ("READY", "merchant"),
    ):
        await client.post(
            f"/api/v1/orders/{order_id}/transitions",
            headers=headers,
            json={"to_status": to_status, "actor": actor},
        )

    partner = await client.post(
        "/api/v1/delivery-partners",
        headers=headers,
        json={"user_id": user_id, "display_name": "Rider One"},
    )
    partner_id = partner.json()["id"]
    await client.post(
        f"/api/v1/delivery-partners/{partner_id}/location",
        headers=headers,
        json={"lat": 12.936, "lng": 77.625, "is_online": True},
    )
    await client.post(
        "/api/v1/vehicles",
        headers=headers,
        json={"partner_id": partner_id, "vehicle_type": "BIKE"},
    )

    ful = await client.get(f"/api/v1/orders/{order_id}/fulfillment", headers=headers)
    fulfillment_id = ful.json()["id"]
    delivery = await client.post(
        f"/api/v1/fulfillments/{fulfillment_id}/deliveries",
        headers=headers,
        json={},
    )
    delivery_id = delivery.json()["id"]
    assigned = await client.post(
        f"/api/v1/deliveries/{delivery_id}/assign",
        headers=headers,
        json={"partner_id": partner_id},
    )
    assert assigned.status_code == 200, assigned.text

    me_partner = await client.get("/api/v1/delivery-partners/me", headers=headers)
    assert me_partner.status_code == 200
    assert me_partner.json()["id"] == partner_id

    my_loc = await client.post(
        "/api/v1/delivery-partners/me/location",
        headers=headers,
        json={"lat": 12.936, "lng": 77.625, "is_online": True},
    )
    assert my_loc.status_code == 200
    assert my_loc.json()["is_online"] is True

    listed = await client.get(
        "/api/v1/deliveries",
        headers=headers,
        params={"mine": True, "active_only": True},
    )
    assert listed.status_code == 200
    assert any(d["id"] == delivery_id for d in listed.json())

    pickup = next(s for s in assigned.json()["stops"] if s["stop_type"] == "PICKUP")
    drop = next(s for s in assigned.json()["stops"] if s["stop_type"] == "DROP")
    await client.post(
        f"/api/v1/deliveries/{delivery_id}/stops/{pickup['id']}/complete",
        headers=headers,
        json={"proof": {"otp": "1111"}},
    )
    done = await client.post(
        f"/api/v1/deliveries/{delivery_id}/stops/{drop['id']}/complete",
        headers=headers,
        json={"proof": {"photo_url": "https://cdn.example/rider.jpg"}},
    )
    assert done.status_code == 200, done.text
    assert done.json()["status"] == "COMPLETED"

    order_final = await client.get(f"/api/v1/orders/{order_id}", headers=headers)
    assert order_final.json()["status"] == "DELIVERED"
