"""Phase 14: hyperlocal golden path with inventory reserve/consume."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

PICKUP_ADDR = {
    "line1": "1 Market St",
    "city": "Bengaluru",
    "state": "KA",
    "pincode": "560001",
}
DROP_ADDR = {
    "line1": "9 Home Rd",
    "city": "Bengaluru",
    "state": "KA",
    "pincode": "560034",
}
PICKUP_LAT, PICKUP_LNG = 12.97, 77.59
DROP_LAT, DROP_LNG = 12.975, 77.595


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
        json={"email": f"{slug}-rider@hyper.example.com", "password": "RiderPass123!"},
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


async def _grocery_store(
    client: AsyncClient, tenant_id: str, slug: str
) -> tuple[str, str, str, str]:
    admin = await _admin_headers(client, tenant_id)
    biz = await client.post(
        "/api/v1/businesses",
        headers=admin,
        json={"name": f"Fresh {slug}", "type": "GROCERY", "status": "ACTIVE"},
    )
    business_id = biz.json()["id"]
    loc = await client.post(
        f"/api/v1/businesses/{business_id}/locations",
        headers=admin,
        json={
            "name": "Store",
            "address": PICKUP_ADDR,
            "lat": PICKUP_LAT,
            "lng": PICKUP_LNG,
        },
    )
    location_id = loc.json()["id"]
    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=admin,
        json={"name": "Rice 1kg"},
    )
    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product.json()['id']}/variants",
        headers=admin,
        json={"name": "Default", "base_price_paise": 12000},
    )
    variant_id = variant.json()["id"]
    inv = await client.post(
        f"/api/v1/businesses/{business_id}/locations/{location_id}/inventory-items",
        headers=admin,
        json={"variant_id": variant_id, "on_hand": 50},
    )
    assert inv.status_code == 200, inv.text
    inventory_item_id = inv.json()["id"]
    return business_id, location_id, variant_id, inventory_item_id


def _settlement_period() -> dict[str, str]:
    now = datetime.now(timezone.utc)
    return {
        "period_start": (now - timedelta(days=1)).isoformat(),
        "period_end": (now + timedelta(days=1)).isoformat(),
    }


async def _transition(client: AsyncClient, headers: dict[str, str], order_id: str, status: str) -> None:
    resp = await client.post(
        f"/api/v1/orders/{order_id}/transition",
        headers=headers,
        json={"to_status": status},
    )
    assert resp.status_code == 200, resp.text


@pytest.mark.asyncio
async def test_hyperlocal_reserve_on_pay_consume_on_deliver(client: AsyncClient) -> None:
    headers = await _tenant_and_customer(client, "p14-golden")
    tenant_id = headers["X-Tenant-ID"]
    admin = await _admin_headers(client, tenant_id)

    business_id, location_id, variant_id, inventory_item_id = await _grocery_store(
        client, tenant_id, "golden"
    )

    cart = await client.post(
        "/api/v1/carts",
        headers=headers,
        json={"business_id": business_id, "location_id": location_id},
    )
    cart_id = cart.json()["id"]
    await client.post(
        f"/api/v1/carts/{cart_id}/items",
        headers=headers,
        json={"variant_id": variant_id, "quantity": 2},
    )

    checkout = await client.post(
        "/api/v1/orders/checkout",
        headers=headers,
        json={"cart_id": cart_id, "fulfillment_type": "DELIVERY"},
    )
    assert checkout.status_code == 200, checkout.text
    order_id = checkout.json()["id"]
    assert checkout.json()["state_machine_profile"] == "HYPERLOCAL_DELIVERY"

    pay = await client.post(
        f"/api/v1/orders/{order_id}/payments",
        headers={**headers, "Idempotency-Key": "p14-pay"},
        json={"provider": "COD"},
    )
    assert pay.status_code == 200, pay.text

    after_reserve = await client.get(
        f"/api/v1/businesses/{business_id}/locations/{location_id}/inventory-items/{inventory_item_id}",
        headers=admin,
    )
    assert after_reserve.json()["reserved"] == 2
    assert after_reserve.json()["available"] == 48

    fulfillment = await client.get(f"/api/v1/orders/{order_id}/fulfillment", headers=admin)
    fulfillment_id = fulfillment.json()["id"]

    for status in ("ACCEPTED", "PICKING", "READY"):
        await _transition(client, admin, order_id, status)

    rider = await _register_rider(client, tenant_id, "p14-golden")
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
                    "address": PICKUP_ADDR,
                    "lat": PICKUP_LAT,
                    "lng": PICKUP_LNG,
                },
                {
                    "sequence": 1,
                    "stop_type": "DROP",
                    "address": DROP_ADDR,
                    "lat": DROP_LAT,
                    "lng": DROP_LNG,
                },
            ],
        },
    )
    delivery_id = delivery.json()["id"]
    stops = delivery.json()["stops"]
    pickup_id = next(s["id"] for s in stops if s["stop_type"] == "PICKUP")
    drop_id = next(s["id"] for s in stops if s["stop_type"] == "DROP")

    await _transition(client, rider, order_id, "PICKED_UP")
    await client.post(
        f"/api/v1/deliveries/{delivery_id}/stops/{pickup_id}/complete",
        headers=rider,
        json={},
    )
    await _transition(client, rider, order_id, "OUT_FOR_DELIVERY")
    await client.post(
        f"/api/v1/deliveries/{delivery_id}/stops/{drop_id}/complete",
        headers=rider,
        json={"proof": {"type": "OTP", "code": "9999"}},
    )
    await _transition(client, rider, order_id, "DELIVERED")

    after_deliver = await client.get(
        f"/api/v1/businesses/{business_id}/locations/{location_id}/inventory-items/{inventory_item_id}",
        headers=admin,
    )
    assert after_deliver.json()["on_hand"] == 48
    assert after_deliver.json()["reserved"] == 0
    assert after_deliver.json()["available"] == 48

    movements = await client.get(
        f"/api/v1/businesses/{business_id}/locations/{location_id}/inventory-items/{inventory_item_id}/movements",
        headers=admin,
    )
    reasons = {m["reason"] for m in movements.json()}
    assert "RESERVE" in reasons
    assert "CONSUME" in reasons

    settlement = await client.post(
        "/api/v1/settlements/calculate",
        headers=admin,
        json={
            "party_type": "MERCHANT",
            "party_id": business_id,
            **(_settlement_period()),
        },
    )
    assert settlement.status_code == 200, settlement.text


@pytest.mark.asyncio
async def test_hyperlocal_cancel_releases_reserved_stock(client: AsyncClient) -> None:
    headers = await _tenant_and_customer(client, "p14-cancel")
    tenant_id = headers["X-Tenant-ID"]
    admin = await _admin_headers(client, tenant_id)

    business_id, location_id, variant_id, inventory_item_id = await _grocery_store(
        client, tenant_id, "cancel"
    )

    cart = await client.post(
        "/api/v1/carts",
        headers=headers,
        json={"business_id": business_id, "location_id": location_id},
    )
    cart_id = cart.json()["id"]
    await client.post(
        f"/api/v1/carts/{cart_id}/items",
        headers=headers,
        json={"variant_id": variant_id, "quantity": 3},
    )

    checkout = await client.post(
        "/api/v1/orders/checkout",
        headers=headers,
        json={"cart_id": cart_id},
    )
    order_id = checkout.json()["id"]

    await client.post(
        f"/api/v1/orders/{order_id}/payments",
        headers={**headers, "Idempotency-Key": "p14-cancel-pay"},
        json={"provider": "COD"},
    )

    reserved = await client.get(
        f"/api/v1/businesses/{business_id}/locations/{location_id}/inventory-items/{inventory_item_id}",
        headers=admin,
    )
    assert reserved.json()["reserved"] == 3

    cancelled = await client.post(
        f"/api/v1/orders/{order_id}/transition",
        headers=admin,
        json={"to_status": "CANCELLED", "reason": "customer request"},
    )
    assert cancelled.status_code == 200, cancelled.text

    after = await client.get(
        f"/api/v1/businesses/{business_id}/locations/{location_id}/inventory-items/{inventory_item_id}",
        headers=admin,
    )
    assert after.json()["reserved"] == 0
    assert after.json()["available"] == 50
