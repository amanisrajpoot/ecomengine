"""Phase 19: admin tenant list and order debugger for ops."""

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
async def test_admin_lists_tenants_and_order_debugger(client: AsyncClient) -> None:
    headers = await _admin_headers(client)
    me = await client.get("/api/v1/auth/me", headers=headers)
    user_id = me.json()["id"]

    tenants_before = await client.get("/api/v1/tenants", headers=headers)
    assert tenants_before.status_code == 200, tenants_before.text
    count_before = len(tenants_before.json())

    tenant = await client.post(
        "/api/v1/tenants",
        headers=headers,
        json={"name": "admin-web", "slug": "admin-web"},
    )
    assert tenant.status_code == 200, tenant.text
    tenant_id = tenant.json()["id"]

    tenants_after = await client.get("/api/v1/tenants", headers=headers)
    assert tenants_after.status_code == 200
    assert len(tenants_after.json()) == count_before + 1
    assert any(t["id"] == tenant_id for t in tenants_after.json())

    headers["X-Tenant-ID"] = tenant_id

    biz = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={"name": "Admin Cafe", "type": "FOOD", "status": "ACTIVE"},
    )
    business_id = biz.json()["id"]
    loc = await client.post(
        f"/api/v1/businesses/{business_id}/locations",
        headers=headers,
        json={
            "name": "Kitchen",
            "address": {
                "line1": "1 Admin St",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pincode": "560001",
            },
            "lat": 12.9784,
            "lng": 77.6408,
        },
    )
    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=headers,
        json={"name": "Thali"},
    )
    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product.json()['id']}/variants",
        headers=headers,
        json={"name": "Full", "base_price_paise": 25000},
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
    fulfillment_id = ful.json()["id"]

    partner = await client.post(
        "/api/v1/delivery-partners",
        headers=headers,
        json={"user_id": user_id, "display_name": "Admin Rider"},
    )
    partner_id = partner.json()["id"]
    await client.post(
        f"/api/v1/delivery-partners/{partner_id}/location",
        headers=headers,
        json={"lat": 12.9790, "lng": 77.6410, "is_online": True},
    )
    await client.post(
        "/api/v1/vehicles",
        headers=headers,
        json={"partner_id": partner_id, "vehicle_type": "BIKE"},
    )

    delivery = await client.post(
        f"/api/v1/fulfillments/{fulfillment_id}/deliveries",
        headers=headers,
        json={"metadata": {"dropoff": {"lat": 12.9884, "lng": 77.6408}}},
    )
    delivery_id = delivery.json()["id"]
    assigned = await client.post(
        f"/api/v1/deliveries/{delivery_id}/assign", headers=headers, json={}
    )
    assert assigned.status_code == 200, assigned.text

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
        json={"proof": {"photo_url": "https://cdn.example/admin-pod.jpg"}},
    )
    assert done.status_code == 200, done.text
    assert done.json()["status"] == "COMPLETED"

    listed = await client.get("/api/v1/orders", headers=headers)
    assert listed.status_code == 200
    assert any(o["id"] == order_id for o in listed.json())

    debug = await client.get(f"/api/v1/orders/{order_id}/debugger", headers=headers)
    assert debug.status_code == 200, debug.text
    body = debug.json()
    assert body["vertical"] == "FOOD"
    assert body["order"]["id"] == order_id
    assert body["order"]["status"] == "DELIVERED"
    assert body["payments"]
    assert body["ledger_entries"]
    assert body["fulfillment"]["status"] == "COMPLETED"
    assert body["delivery"]["status"] == "COMPLETED"
    assert "order" in body["chain"] and "settlements" in body["chain"]
