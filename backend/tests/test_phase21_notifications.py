"""Phase 21: order lifecycle SMS notifications via event bus."""

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
async def test_order_checkout_sends_sms_notifications(client: AsyncClient) -> None:
    headers = await _admin_headers(client)
    tenant = await client.post(
        "/api/v1/tenants",
        headers=headers,
        json={"name": "notify-tenant", "slug": "notify-tenant"},
    )
    tenant_id = tenant.json()["id"]
    headers["X-Tenant-ID"] = tenant_id

    biz = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={"name": "Notify Cafe", "type": "FOOD", "status": "ACTIVE"},
    )
    business_id = biz.json()["id"]
    loc = await client.post(
        f"/api/v1/businesses/{business_id}/locations",
        headers=headers,
        json={
            "name": "Kitchen",
            "address": {
                "line1": "1 Main",
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
        json={"name": "Meal"},
    )
    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product.json()['id']}/variants",
        headers=headers,
        json={"name": "Box", "base_price_paise": 15000},
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
        json={
            "cart_id": cart.json()["id"],
            "payment_provider": "cod",
            "customer_phone": "9876512345",
        },
    )
    assert checkout.status_code == 200, checkout.text
    order_id = checkout.json()["id"]

    notes = await client.get(
        "/api/v1/notifications",
        headers=headers,
        params={"order_id": order_id},
    )
    assert notes.status_code == 200, notes.text
    rows = notes.json()
    assert len(rows) >= 2
    assert all(n["recipient"] == "9876512345" for n in rows)
    assert all(n["status"] == "SENT" for n in rows)
    assert all(n["channel"] == "sms" for n in rows)
    events = {n["event_name"] for n in rows}
    assert "OrderCreated" in events
    assert "PaymentCaptured" in events

    await client.post(
        f"/api/v1/orders/{order_id}/transitions",
        headers=headers,
        json={"to_status": "ACCEPTED", "actor": "merchant"},
    )
    notes2 = await client.get(
        "/api/v1/notifications",
        headers=headers,
        params={"order_id": order_id},
    )
    assert any(n["event_name"] == "OrderAccepted" for n in notes2.json())
