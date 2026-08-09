"""Phase 24: auto-dispatch on OrderReady / courier PaymentCaptured."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _admin_headers(client: AsyncClient) -> dict[str, str]:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _ready_order(client: AsyncClient, slug: str) -> tuple[dict[str, str], str, str]:
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
            "location_id": loc.json()["id"],
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
    order_id = checkout.json()["id"]

    partner = await client.post(
        "/api/v1/delivery-partners",
        headers=headers,
        json={"user_id": user_id, "display_name": "Auto Rider"},
    )
    partner_id = partner.json()["id"]
    await client.post(
        f"/api/v1/delivery-partners/{partner_id}/location",
        headers=headers,
        json={"lat": 12.9360, "lng": 77.6250, "is_online": True},
    )
    await client.post(
        "/api/v1/vehicles",
        headers=headers,
        json={"partner_id": partner_id, "vehicle_type": "BIKE"},
    )

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

    return headers, order_id, partner_id


@pytest.mark.asyncio
async def test_auto_dispatch_on_order_ready(client: AsyncClient) -> None:
    """Marking READY auto-creates delivery and assigns nearest online rider."""
    headers, order_id, partner_id = await _ready_order(client, "auto-dispatch")

    ful = await client.get(f"/api/v1/orders/{order_id}/fulfillment", headers=headers)
    assert ful.status_code == 200
    assert ful.json()["status"] == "AWAITING_PICKUP"

    delivery = await client.get(
        f"/api/v1/fulfillments/{ful.json()['id']}/delivery",
        headers=headers,
    )
    assert delivery.status_code == 200, delivery.text
    body = delivery.json()
    assert body["status"] == "ASSIGNED"
    assert body["partner_id"] == partner_id

    listed = await client.get(
        "/api/v1/deliveries",
        headers=headers,
        params={"partner_id": partner_id, "active_only": True},
    )
    assert listed.status_code == 200
    assert any(d["id"] == body["id"] for d in listed.json())


@pytest.mark.asyncio
async def test_merchant_can_request_rider_via_api(client: AsyncClient) -> None:
    """Manual dispatch API works when auto-dispatch skipped (no rider online)."""
    headers = await _admin_headers(client)
    me = await client.get("/api/v1/auth/me", headers=headers)
    user_id = me.json()["id"]

    tenant = await client.post(
        "/api/v1/tenants",
        headers=headers,
        json={"name": "manual-dispatch", "slug": "manual-dispatch"},
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
            "address": {"line1": "12 Main", "city": "Bengaluru", "state": "KA", "pincode": "560095"},
            "lat": 12.9352,
            "lng": 77.6245,
        },
    )
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
    for to_status, actor in (("ACCEPTED", "merchant"), ("PREPARING", "merchant"), ("READY", "merchant")):
        await client.post(
            f"/api/v1/orders/{order_id}/transitions",
            headers=headers,
            json={"to_status": to_status, "actor": actor},
        )

    ful = await client.get(f"/api/v1/orders/{order_id}/fulfillment", headers=headers)
    delivery = await client.get(
        f"/api/v1/fulfillments/{ful.json()['id']}/delivery",
        headers=headers,
    )
    assert delivery.status_code == 200
    assert delivery.json()["status"] == "CREATED"
    assert delivery.json()["partner_id"] is None

    partner = await client.post(
        "/api/v1/delivery-partners",
        headers=headers,
        json={"user_id": user_id, "display_name": "Late Rider"},
    )
    await client.post(
        f"/api/v1/delivery-partners/{partner.json()['id']}/location",
        headers=headers,
        json={"lat": 12.936, "lng": 77.625, "is_online": True},
    )
    await client.post(
        "/api/v1/vehicles",
        headers=headers,
        json={"partner_id": partner.json()["id"], "vehicle_type": "BIKE"},
    )

    assigned = await client.post(
        f"/api/v1/deliveries/{delivery.json()['id']}/assign",
        headers=headers,
        json={},
    )
    assert assigned.status_code == 200, assigned.text
    assert assigned.json()["partner_id"] == partner.json()["id"]
