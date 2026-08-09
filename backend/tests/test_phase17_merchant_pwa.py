"""Phase 17: merchant order queue and kitchen transitions."""

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
async def test_merchant_lists_and_advances_food_order(client: AsyncClient) -> None:
    headers = await _admin_headers(client)
    tenant = await client.post(
        "/api/v1/tenants",
        headers=headers,
        json={"name": "merchant-pwa", "slug": "merchant-pwa"},
    )
    tenant_id = tenant.json()["id"]
    headers["X-Tenant-ID"] = tenant_id

    biz = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={"name": "Queue Kitchen", "type": "FOOD", "status": "ACTIVE"},
    )
    business_id = biz.json()["id"]
    loc = await client.post(
        f"/api/v1/businesses/{business_id}/locations",
        headers=headers,
        json={
            "name": "Main",
            "address": {
                "line1": "1 St",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pincode": "560001",
            },
            "lat": 12.97,
            "lng": 77.59,
        },
    )
    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=headers,
        json={"name": "Dosa"},
    )
    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product.json()['id']}/variants",
        headers=headers,
        json={"name": "Plain", "base_price_paise": 5000},
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
    assert checkout.json()["status"] == "PAYMENT_CONFIRMED"

    listed = await client.get(
        "/api/v1/orders",
        headers=headers,
        params={"business_id": business_id},
    )
    assert listed.status_code == 200
    assert any(o["id"] == order_id for o in listed.json())

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

    final = await client.get(f"/api/v1/orders/{order_id}", headers=headers)
    assert final.json()["status"] == "READY"

    ful = await client.get(f"/api/v1/orders/{order_id}/fulfillment", headers=headers)
    assert ful.status_code == 200
    assert ful.json()["status"] == "AWAITING_PICKUP"
