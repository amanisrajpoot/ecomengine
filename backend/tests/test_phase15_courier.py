"""Phase 15: courier quote, MULTI_STOP fulfillment, POD, settlement."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

PICKUP = {
    "lat": 12.9716,
    "lng": 77.5946,
    "address": {"line1": "Tower A", "city": "Bengaluru", "state": "KA", "pincode": "560001"},
}
DROP = {
    "lat": 12.9816,
    "lng": 77.6046,
    "address": {"line1": "Tower B", "city": "Bengaluru", "state": "KA", "pincode": "560034"},
}


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
        json={"email": f"{slug}-rider@courier.example.com", "password": "RiderPass123!"},
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
async def test_courier_quote_formula(client: AsyncClient) -> None:
    headers = await _tenant_and_customer(client, "p15-quote")
    admin = await _admin_headers(client, headers["X-Tenant-ID"])

    biz = await client.post(
        "/api/v1/businesses",
        headers=admin,
        json={"name": "Quick Courier", "type": "COURIER", "status": "ACTIVE"},
    )
    business_id = biz.json()["id"]

    quote = await client.post(
        "/api/v1/courier/quote",
        headers=headers,
        json={
            "business_id": business_id,
            "pickup": PICKUP,
            "drop": DROP,
            "weight_kg": 2.0,
            "vehicle_type": "BIKE",
            "express": False,
        },
    )
    assert quote.status_code == 200, quote.text
    breakdown = quote.json()["breakdown"]
    assert breakdown["delivery_fee_paise"] == 0
    assert breakdown["subtotal_paise"] > 5000
    assert breakdown["total_paise"] == (
        breakdown["subtotal_paise"]
        + breakdown["platform_fee_paise"]
        + breakdown["tax_paise"]
    )


@pytest.mark.golden
@pytest.mark.asyncio
async def test_courier_golden_path_to_settlement(client: AsyncClient) -> None:
    headers = await _tenant_and_customer(client, "p15-golden")
    tenant_id = headers["X-Tenant-ID"]
    admin = await _admin_headers(client, tenant_id)

    biz = await client.post(
        "/api/v1/businesses",
        headers=admin,
        json={"name": "City Courier", "type": "COURIER", "status": "ACTIVE"},
    )
    business_id = biz.json()["id"]

    quote = await client.post(
        "/api/v1/courier/quote",
        headers=headers,
        json={
            "business_id": business_id,
            "pickup": PICKUP,
            "drop": DROP,
            "weight_kg": 1.5,
            "vehicle_type": "BIKE",
        },
    )
    quote_body = quote.json()
    line_meta = quote_body["quote"]
    total_paise = quote_body["breakdown"]["total_paise"]

    cart = await client.post(
        "/api/v1/carts",
        headers=headers,
        json={"business_id": business_id},
    )
    cart_id = cart.json()["id"]
    await client.post(
        f"/api/v1/carts/{cart_id}/items",
        headers=headers,
        json={"quantity": 1, "meta": line_meta},
    )

    checkout = await client.post(
        "/api/v1/orders/checkout",
        headers=headers,
        json={"cart_id": cart_id, "fulfillment_type": "MULTI_STOP"},
    )
    assert checkout.status_code == 200, checkout.text
    order_id = checkout.json()["id"]
    assert checkout.json()["state_machine_profile"] == "COURIER"

    fulfillment = await client.get(f"/api/v1/orders/{order_id}/fulfillment", headers=admin)
    assert fulfillment.json()["type"] == "MULTI_STOP"
    fulfillment_id = fulfillment.json()["id"]

    pay = await client.post(
        f"/api/v1/orders/{order_id}/payments",
        headers={**headers, "Idempotency-Key": "p15-courier-pay"},
        json={"provider": "COD"},
    )
    assert pay.status_code == 200, pay.text

    await _transition(client, admin, order_id, "PICKUP_ASSIGNED")

    rider = await _register_rider(client, tenant_id, "p15-golden")
    await client.post("/api/v1/partners/profiles", headers=rider, json={})
    await client.patch(
        "/api/v1/partners/profiles/me",
        headers=rider,
        json={"is_online": True, "current_lat": PICKUP["lat"], "current_lng": PICKUP["lng"]},
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
                    "address": PICKUP["address"],
                    "lat": PICKUP["lat"],
                    "lng": PICKUP["lng"],
                },
                {
                    "sequence": 1,
                    "stop_type": "DROP",
                    "address": DROP["address"],
                    "lat": DROP["lat"],
                    "lng": DROP["lng"],
                },
            ],
        },
    )
    assert delivery.status_code == 200, delivery.text
    delivery_id = delivery.json()["id"]
    stops = delivery.json()["stops"]
    pickup_id = next(s["id"] for s in stops if s["stop_type"] == "PICKUP")
    drop_id = next(s["id"] for s in stops if s["stop_type"] == "DROP")

    await _transition(client, rider, order_id, "PICKED_UP")
    await client.post(
        f"/api/v1/deliveries/{delivery_id}/stops/{pickup_id}/complete",
        headers=rider,
        json={"proof": {"type": "OTP", "code": "1111"}},
    )
    await _transition(client, rider, order_id, "IN_TRANSIT")
    await client.post(
        f"/api/v1/deliveries/{delivery_id}/stops/{drop_id}/complete",
        headers=rider,
        json={"proof": {"type": "SIGNATURE", "signed_by": "Receiver"}},
    )
    await _transition(client, rider, order_id, "DELIVERED")

    order = await client.get(f"/api/v1/orders/{order_id}", headers=headers)
    assert order.json()["status"] == "DELIVERED"

    ledger = await client.get(f"/api/v1/orders/{order_id}/ledger-entries", headers=admin)
    assert len(ledger.json()) == 1

    merchant_settlement = await client.post(
        "/api/v1/settlements/calculate",
        headers=admin,
        json={
            "party_type": "MERCHANT",
            "party_id": business_id,
            **(_settlement_period()),
        },
    )
    assert merchant_settlement.status_code == 200, merchant_settlement.text

    platform_settlement = await client.post(
        "/api/v1/settlements/calculate",
        headers=admin,
        json={
            "party_type": "PLATFORM",
            "party_id": tenant_id,
            **(_settlement_period()),
        },
    )
    assert platform_settlement.status_code == 200, platform_settlement.text
    assert pay.json()["amount_paise"] == total_paise
