"""Phase 15: Courier vertical — quote by distance/weight/vehicle → POD → settle."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from app.verticals.courier import (
    COURIER_DEFAULT_FULFILLMENT,
    COURIER_STATE_MACHINE_PROFILE,
    GOLDEN_PATH_STEPS,
)


def test_courier_vertical_config() -> None:
    assert COURIER_STATE_MACHINE_PROFILE == "COURIER"
    assert COURIER_DEFAULT_FULFILLMENT == "MULTI_STOP"
    assert "quote_by_distance_weight_vehicle" in GOLDEN_PATH_STEPS
    assert "pod_delivered" in GOLDEN_PATH_STEPS


async def _admin_headers(client: AsyncClient) -> dict[str, str]:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.mark.asyncio
async def test_courier_golden_path_end_to_end(client: AsyncClient) -> None:
    """Quote → COD shipment → assign → pickup → transit → POD → ledger → settle."""
    headers = await _admin_headers(client)
    me = await client.get("/api/v1/auth/me", headers=headers)
    user_id = me.json()["id"]

    tenant = await client.post(
        "/api/v1/tenants",
        headers=headers,
        json={"name": "courier-golden", "slug": "courier-golden"},
    )
    assert tenant.status_code == 200, tenant.text
    tenant_id = tenant.json()["id"]
    headers["X-Tenant-ID"] = tenant_id

    biz = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={
            "name": "CityDash Courier",
            "type": "COURIER",
            "status": "ACTIVE",
            "settings": {"currency": "INR"},
        },
    )
    assert biz.status_code == 200, biz.text
    assert biz.json()["capabilities"]["catalog"] is False
    assert biz.json()["capabilities"]["delivery"] is True
    business_id = biz.json()["id"]

    pickup = {
        "lat": 12.9716,
        "lng": 77.5946,
        "address": {
            "line1": "MG Road Hub",
            "city": "Bengaluru",
            "state": "Karnataka",
            "pincode": "560001",
        },
        "contact": {"name": "Sender", "phone": "9000000001"},
    }
    drop = {
        "lat": 12.9352,
        "lng": 77.6245,
        "address": {
            "line1": "Koramangala 5th Block",
            "city": "Bengaluru",
            "state": "Karnataka",
            "pincode": "560095",
        },
        "contact": {"name": "Receiver", "phone": "9000000002"},
    }

    # 1) Quote by distance / weight / vehicle
    quote = await client.post(
        "/api/v1/courier/quote",
        headers=headers,
        json={
            "pickup": pickup,
            "drop": drop,
            "weight_kg": 2.5,
            "vehicle_type": "BIKE",
            "express": False,
            "business_id": business_id,
        },
    )
    assert quote.status_code == 200, quote.text
    q = quote.json()
    assert q["distance_km"] > 0
    assert q["pricing"]["total_paise"] > q["pricing"]["subtotal_paise"]
    assert q["fare_components"]["base_fare_paise"] > 0
    assert q["fare_components"]["distance_paise"] > 0
    assert q["fare_components"]["weight_paise"] > 0

    express = await client.post(
        "/api/v1/courier/quote",
        headers=headers,
        json={
            "pickup": pickup,
            "drop": drop,
            "weight_kg": 2.5,
            "vehicle_type": "VAN",
            "express": True,
        },
    )
    assert express.status_code == 200
    assert express.json()["pricing"]["subtotal_paise"] > q["pricing"]["subtotal_paise"]

    # 2) Shipment checkout (COD) — shared Order, no catalog
    shipment = await client.post(
        "/api/v1/courier/shipments",
        headers=headers,
        json={
            "business_id": business_id,
            "pickup": pickup,
            "drop": drop,
            "weight_kg": 2.5,
            "vehicle_type": "BIKE",
            "package_notes": "Documents",
            "payment_provider": "cod",
            "customer_phone": "9876543210",
        },
    )
    assert shipment.status_code == 200, shipment.text
    order = shipment.json()
    order_id = order["id"]
    assert order["state_machine_profile"] == "COURIER"
    assert order["fulfillment_type"] == "MULTI_STOP"
    assert order["status"] == "PAYMENT_CONFIRMED"
    assert order["metadata"]["package"]["weight_kg"] == 2.5
    assert order["pricing_snapshot"]["courier"]["distance_km"] > 0
    assert order["items"][0]["variant_id"] is None

    ledger = await client.get(f"/api/v1/orders/{order_id}/ledger", headers=headers)
    assert ledger.status_code == 200
    assert any(e["account"] == "MERCHANT_PAYABLE" for e in ledger.json())

    ful = await client.get(f"/api/v1/orders/{order_id}/fulfillment", headers=headers)
    assert ful.status_code == 200
    fulfillment_id = ful.json()["id"]
    assert ful.json()["type"] == "MULTI_STOP"
    assert ful.json()["status"] == "PENDING"

    # 3) Create delivery (auto hop MULTI_STOP to READY) + assign rider
    partner = await client.post(
        "/api/v1/delivery-partners",
        headers=headers,
        json={"user_id": user_id, "display_name": "Courier Rider"},
    )
    partner_id = partner.json()["id"]
    await client.post(
        f"/api/v1/delivery-partners/{partner_id}/location",
        headers=headers,
        json={"lat": 12.9720, "lng": 77.5950, "is_online": True},
    )
    await client.post(
        "/api/v1/vehicles",
        headers=headers,
        json={"partner_id": partner_id, "vehicle_type": "BIKE"},
    )

    delivery = await client.post(
        f"/api/v1/fulfillments/{fulfillment_id}/deliveries",
        headers=headers,
        json={},
    )
    assert delivery.status_code == 200, delivery.text
    delivery_id = delivery.json()["id"]
    stops = delivery.json()["stops"]
    assert len(stops) == 2
    assert {s["stop_type"] for s in stops} == {"PICKUP", "DROP"}
    pickup_stop = next(s for s in stops if s["stop_type"] == "PICKUP")
    drop_stop = next(s for s in stops if s["stop_type"] == "DROP")
    assert abs(pickup_stop["lat"] - pickup["lat"]) < 0.001
    assert abs(drop_stop["lat"] - drop["lat"]) < 0.001

    assigned = await client.post(
        f"/api/v1/deliveries/{delivery_id}/assign", headers=headers, json={}
    )
    assert assigned.status_code == 200, assigned.text
    assert assigned.json()["partner_id"] == partner_id
    assert assigned.json()["status"] == "ASSIGNED"

    order_assigned = await client.get(f"/api/v1/orders/{order_id}", headers=headers)
    assert order_assigned.json()["status"] == "PICKUP_ASSIGNED"

    # 4) Pickup + drop POD → DELIVERED via courier path
    await client.post(
        f"/api/v1/deliveries/{delivery_id}/stops/{pickup_stop['id']}/complete",
        headers=headers,
        json={"proof": {"otp": "2222"}},
    )
    done = await client.post(
        f"/api/v1/deliveries/{delivery_id}/stops/{drop_stop['id']}/complete",
        headers=headers,
        json={"proof": {"photo_url": "https://cdn.example/courier-pod.jpg", "otp": "3333"}},
    )
    assert done.status_code == 200, done.text
    assert done.json()["status"] == "COMPLETED"

    order_final = await client.get(f"/api/v1/orders/{order_id}", headers=headers)
    assert order_final.json()["status"] == "DELIVERED"

    ful_final = await client.get(f"/api/v1/orders/{order_id}/fulfillment", headers=headers)
    assert ful_final.json()["status"] == "COMPLETED"

    # 5) Settlements
    period = {
        "period_start": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
        "period_end": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
    }
    merchant_s = await client.post(
        "/api/v1/settlements",
        headers=headers,
        json={"party_type": "MERCHANT", "party_id": business_id, **period},
    )
    assert merchant_s.status_code == 200
    calc_m = await client.post(
        f"/api/v1/settlements/{merchant_s.json()['id']}/calculate", headers=headers
    )
    assert calc_m.status_code == 200
    assert calc_m.json()["total_paise"] > 0

    # 6) Debugger vertical = COURIER
    debug = await client.get(f"/api/v1/orders/{order_id}/debugger", headers=headers)
    assert debug.status_code == 200, debug.text
    body = debug.json()
    assert body["vertical"] == "COURIER"
    assert body["order"]["status"] == "DELIVERED"
    assert body["fulfillment"]["type"] == "MULTI_STOP"
    assert body["delivery"]["status"] == "COMPLETED"
