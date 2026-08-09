"""Phase 14: Hyperlocal vertical — discovery + inventory reserve/consume golden path."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from app.verticals.hyperlocal import (
    GOLDEN_PATH_STEPS,
    HYPERLOCAL_DEFAULT_FULFILLMENT,
    HYPERLOCAL_STATE_MACHINE_PROFILE,
    HYPERLOCAL_TYPES,
)


def test_hyperlocal_vertical_config() -> None:
    assert HYPERLOCAL_STATE_MACHINE_PROFILE == "HYPERLOCAL_DELIVERY"
    assert HYPERLOCAL_DEFAULT_FULFILLMENT == "DELIVERY"
    assert "GROCERY" in HYPERLOCAL_TYPES
    assert "discover_nearby_store" in GOLDEN_PATH_STEPS
    assert "checkout_pay_reserves_stock" in GOLDEN_PATH_STEPS


async def _admin_headers(client: AsyncClient) -> dict[str, str]:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.mark.asyncio
async def test_hyperlocal_golden_path_end_to_end(client: AsyncClient) -> None:
    """Discover → stock → cart → COD reserve → pick → deliver consume → settle."""
    headers = await _admin_headers(client)
    me = await client.get("/api/v1/auth/me", headers=headers)
    user_id = me.json()["id"]

    tenant = await client.post(
        "/api/v1/tenants",
        headers=headers,
        json={"name": "hyper-golden", "slug": "hyper-golden"},
    )
    assert tenant.status_code == 200, tenant.text
    tenant_id = tenant.json()["id"]
    headers["X-Tenant-ID"] = tenant_id

    # 1) Grocery store with service radius
    biz = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={
            "name": "FreshMart Indiranagar",
            "type": "GROCERY",
            "status": "ACTIVE",
            "settings": {"currency": "INR"},
        },
    )
    assert biz.status_code == 200, biz.text
    assert biz.json()["capabilities"]["inventory"] is True
    assert biz.json()["capabilities"]["delivery"] is True
    business_id = biz.json()["id"]

    loc = await client.post(
        f"/api/v1/businesses/{business_id}/locations",
        headers=headers,
        json={
            "name": "Indiranagar Store",
            "address": {
                "line1": "12 12th Main",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pincode": "560038",
            },
            "lat": 12.9784,
            "lng": 77.6408,
            "service_area": {"type": "radius", "radius_km": 5},
            "hours": [{"day": "mon", "open": "08:00", "close": "22:00"}],
        },
    )
    assert loc.status_code == 200, loc.text
    location_id = loc.json()["id"]

    nearby = await client.get(
        "/api/v1/stores/nearby",
        headers=headers,
        params={"lat": 12.9790, "lng": 77.6410, "radius_km": 5, "type": "GROCERY"},
    )
    assert nearby.status_code == 200, nearby.text
    stores = nearby.json()
    assert any(s["location_id"] == location_id for s in stores)
    assert stores[0]["distance_km"] >= 0

    far = await client.get(
        "/api/v1/stores/nearby",
        headers=headers,
        params={"lat": 13.05, "lng": 77.75, "radius_km": 1, "type": "GROCERY"},
    )
    assert far.status_code == 200
    assert all(s["location_id"] != location_id for s in far.json())

    # 2) Catalog + inventory receive
    cat = await client.post(
        f"/api/v1/businesses/{business_id}/categories",
        headers=headers,
        json={"name": "Dairy"},
    )
    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=headers,
        json={"name": "Milk 1L", "category_id": cat.json()["id"]},
    )
    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product.json()['id']}/variants",
        headers=headers,
        json={"name": "Default", "base_price_paise": 6500, "sku": "MILK-1L"},
    )
    variant_id = variant.json()["id"]

    inv = await client.post(
        f"/api/v1/businesses/{business_id}/inventory",
        headers=headers,
        json={
            "location_id": location_id,
            "variant_id": variant_id,
            "low_stock_threshold": 2,
        },
    )
    assert inv.status_code == 200, inv.text
    item_id = inv.json()["id"]
    received = await client.post(
        f"/api/v1/businesses/{business_id}/inventory/{item_id}/adjust",
        headers=headers,
        json={"delta_on_hand": 10, "reason": "RECEIVE", "note": "PO-hyper"},
    )
    assert received.status_code == 200, received.text
    assert received.json()["available"] == 10

    # 3) Cart + COD checkout → reserve on PAYMENT_CONFIRMED
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
    cart_id = cart.json()["id"]
    item = await client.post(
        f"/api/v1/carts/{cart_id}/items",
        headers=headers,
        json={"variant_id": variant_id, "quantity": 2},
    )
    assert item.status_code == 200, item.text

    checkout = await client.post(
        "/api/v1/orders/checkout",
        headers=headers,
        json={
            "cart_id": cart_id,
            "payment_provider": "cod",
            "fulfillment_type": "DELIVERY",
            "customer_phone": "9876543210",
        },
    )
    assert checkout.status_code == 200, checkout.text
    order = checkout.json()
    order_id = order["id"]
    assert order["state_machine_profile"] == "HYPERLOCAL_DELIVERY"
    assert order["status"] == "PAYMENT_CONFIRMED"

    stock = await client.get(
        f"/api/v1/businesses/{business_id}/inventory/{item_id}", headers=headers
    )
    assert stock.status_code == 200, stock.text
    assert stock.json()["on_hand"] == 10
    assert stock.json()["reserved"] == 2
    assert stock.json()["available"] == 8

    ledger = await client.get(f"/api/v1/orders/{order_id}/ledger", headers=headers)
    assert ledger.status_code == 200
    assert any(e["account"] == "MERCHANT_PAYABLE" for e in ledger.json())

    ful = await client.get(f"/api/v1/orders/{order_id}/fulfillment", headers=headers)
    assert ful.status_code == 200
    fulfillment_id = ful.json()["id"]

    # 4) Accept → picking → ready
    for to_status, actor in (
        ("ACCEPTED", "merchant"),
        ("PICKING", "staff"),
        ("READY", "staff"),
    ):
        resp = await client.post(
            f"/api/v1/orders/{order_id}/transitions",
            headers=headers,
            json={"to_status": to_status, "actor": actor},
        )
        assert resp.status_code == 200, resp.text

    # 5) Rider deliver → consume reserved stock
    partner = await client.post(
        "/api/v1/delivery-partners",
        headers=headers,
        json={"user_id": user_id, "display_name": "Hyper Rider"},
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
    assert delivery.status_code == 200, delivery.text
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
        json={"proof": {"photo_url": "https://cdn.example/hyper-pod.jpg"}},
    )
    assert done.status_code == 200, done.text
    assert done.json()["status"] == "COMPLETED"

    order_final = await client.get(f"/api/v1/orders/{order_id}", headers=headers)
    assert order_final.json()["status"] == "DELIVERED"

    stock_after = await client.get(
        f"/api/v1/businesses/{business_id}/inventory/{item_id}", headers=headers
    )
    assert stock_after.json()["on_hand"] == 8
    assert stock_after.json()["reserved"] == 0
    assert stock_after.json()["available"] == 8

    # 6) Settlements
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

    # 7) Debugger vertical = HYPERLOCAL
    debug = await client.get(f"/api/v1/orders/{order_id}/debugger", headers=headers)
    assert debug.status_code == 200, debug.text
    body = debug.json()
    assert body["vertical"] == "HYPERLOCAL"
    assert body["order"]["status"] == "DELIVERED"
    assert body["fulfillment"]["status"] == "COMPLETED"
    assert body["delivery"]["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_hyperlocal_cancel_releases_reservation(client: AsyncClient) -> None:
    headers = await _admin_headers(client)
    tenant = await client.post(
        "/api/v1/tenants",
        headers=headers,
        json={"name": "hyper-cancel", "slug": "hyper-cancel"},
    )
    headers["X-Tenant-ID"] = tenant.json()["id"]

    biz = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={"name": "CancelMart", "type": "GROCERY", "status": "ACTIVE"},
    )
    business_id = biz.json()["id"]
    loc = await client.post(
        f"/api/v1/businesses/{business_id}/locations",
        headers=headers,
        json={
            "name": "Main",
            "address": {
                "line1": "1 MG Road",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pincode": "560001",
            },
            "lat": 12.97,
            "lng": 77.59,
            "service_area": {"type": "radius", "radius_km": 8},
        },
    )
    location_id = loc.json()["id"]
    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=headers,
        json={"name": "Eggs"},
    )
    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product.json()['id']}/variants",
        headers=headers,
        json={"name": "Dozen", "base_price_paise": 8000},
    )
    inv = await client.post(
        f"/api/v1/businesses/{business_id}/inventory",
        headers=headers,
        json={"location_id": location_id, "variant_id": variant.json()["id"]},
    )
    item_id = inv.json()["id"]
    await client.post(
        f"/api/v1/businesses/{business_id}/inventory/{item_id}/adjust",
        headers=headers,
        json={"delta_on_hand": 5, "reason": "RECEIVE"},
    )

    cart = await client.post(
        "/api/v1/carts",
        headers=headers,
        json={"business_id": business_id, "location_id": location_id},
    )
    await client.post(
        f"/api/v1/carts/{cart.json()['id']}/items",
        headers=headers,
        json={"variant_id": variant.json()["id"], "quantity": 3},
    )
    checkout = await client.post(
        "/api/v1/orders/checkout",
        headers=headers,
        json={
            "cart_id": cart.json()["id"],
            "payment_provider": "cod",
            "fulfillment_type": "DELIVERY",
        },
    )
    assert checkout.status_code == 200, checkout.text
    order_id = checkout.json()["id"]

    stock = await client.get(
        f"/api/v1/businesses/{business_id}/inventory/{item_id}", headers=headers
    )
    assert stock.json()["reserved"] == 3

    cancel = await client.post(
        f"/api/v1/orders/{order_id}/transitions",
        headers=headers,
        json={"to_status": "CANCELLED", "actor": "customer", "reason": "changed_mind"},
    )
    assert cancel.status_code == 200, cancel.text

    stock_after = await client.get(
        f"/api/v1/businesses/{business_id}/inventory/{item_id}", headers=headers
    )
    assert stock_after.json()["on_hand"] == 5
    assert stock_after.json()["reserved"] == 0
    assert stock_after.json()["available"] == 5
