"""Phase 13: Food vertical golden path (shared engines, no FoodOrder)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from app.verticals.food import (
    FOOD_DEFAULT_FULFILLMENT,
    FOOD_STATE_MACHINE_PROFILE,
    GOLDEN_PATH_STEPS,
)


def test_food_vertical_config() -> None:
    assert FOOD_STATE_MACHINE_PROFILE == "FOOD_DELIVERY"
    assert FOOD_DEFAULT_FULFILLMENT == "DELIVERY"
    assert "settlement_calculated" in GOLDEN_PATH_STEPS


async def _admin_headers(client: AsyncClient) -> dict[str, str]:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.mark.asyncio
async def test_food_golden_path_end_to_end(client: AsyncClient) -> None:
    """Acceptance: FOOD business → addons → cart → pay → cook → rider → ledger → settle."""
    headers = await _admin_headers(client)
    me = await client.get("/api/v1/auth/me", headers=headers)
    user_id = me.json()["id"]

    tenant = await client.post(
        "/api/v1/tenants",
        headers=headers,
        json={"name": "food-golden", "slug": "food-golden"},
    )
    assert tenant.status_code == 200, tenant.text
    tenant_id = tenant.json()["id"]
    headers["X-Tenant-ID"] = tenant_id

    # 1) Restaurant
    biz = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={
            "name": "Spice Kitchen",
            "type": "FOOD",
            "status": "ACTIVE",
            "settings": {"preparation_time_minutes": 20, "currency": "INR"},
        },
    )
    assert biz.status_code == 200, biz.text
    assert biz.json()["capabilities"]["addons"] is True
    assert biz.json()["capabilities"]["delivery"] is True
    business_id = biz.json()["id"]

    loc = await client.post(
        f"/api/v1/businesses/{business_id}/locations",
        headers=headers,
        json={
            "name": "Indiranagar",
            "address": {
                "line1": "100 100 Feet Rd",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pincode": "560038",
            },
            "lat": 12.9784,
            "lng": 77.6408,
            "hours": [{"day": "mon", "open": "10:00", "close": "23:00"}],
        },
    )
    assert loc.status_code == 200, loc.text
    location_id = loc.json()["id"]

    # 2) Catalog with addons
    cat = await client.post(
        f"/api/v1/businesses/{business_id}/categories",
        headers=headers,
        json={"name": "Mains"},
    )
    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=headers,
        json={"name": "Butter Chicken", "category_id": cat.json()["id"]},
    )
    assert product.status_code == 200, product.text
    product_id = product.json()["id"]
    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product_id}/variants",
        headers=headers,
        json={"name": "Regular", "base_price_paise": 29900},
    )
    addon = await client.post(
        f"/api/v1/businesses/{business_id}/addons",
        headers=headers,
        json={"name": "Extra Butter", "price_paise": 3000, "max_qty": 2},
    )
    assert addon.status_code == 200, addon.text
    link = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product_id}/addons",
        headers=headers,
        json={"addon_id": addon.json()["id"], "group_name": "extras"},
    )
    assert link.status_code == 200, link.text

    # 3) Cart + price (addons in snapshot)
    cart = await client.post(
        "/api/v1/carts",
        headers=headers,
        json={
            "business_id": business_id,
            "location_id": location_id,
            "delivery_fee_paise": 4000,
            "platform_fee_paise": 500,
        },
    )
    cart_id = cart.json()["id"]
    item = await client.post(
        f"/api/v1/carts/{cart_id}/items",
        headers=headers,
        json={
            "variant_id": variant.json()["id"],
            "quantity": 1,
            "addons": [{"addon_id": addon.json()["id"], "quantity": 1}],
        },
    )
    assert item.status_code == 200, item.text
    priced = await client.get(f"/api/v1/carts/{cart_id}", headers=headers)
    snap = priced.json()["pricing_snapshot"]
    assert snap["subtotal_paise"] >= 32900  # 29900 + 3000 addon
    assert snap["total_paise"] > snap["subtotal_paise"]

    # 4) Checkout COD → pay confirmed + ledger + fulfillment
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
    assert order["state_machine_profile"] == "FOOD_DELIVERY"
    assert order["status"] == "PAYMENT_CONFIRMED"
    assert order["items"][0]["addons_snapshot"]
    assert any(a.get("name") == "Extra Butter" for a in order["items"][0]["addons_snapshot"])

    ledger = await client.get(f"/api/v1/orders/{order_id}/ledger", headers=headers)
    assert ledger.status_code == 200
    assert ledger.json()
    assert any(e["account"] == "MERCHANT_PAYABLE" for e in ledger.json())

    ful = await client.get(f"/api/v1/orders/{order_id}/fulfillment", headers=headers)
    assert ful.status_code == 200
    assert ful.json()["status"] == "PENDING"
    fulfillment_id = ful.json()["id"]

    # 5) Merchant accept → prepare → ready
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
    assert ful.json()["status"] == "READY"

    # 6) Rider assign + deliver
    partner = await client.post(
        "/api/v1/delivery-partners",
        headers=headers,
        json={"user_id": user_id, "display_name": "Food Rider"},
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
    assert assigned.json()["partner_id"] == partner_id

    pickup = next(s for s in assigned.json()["stops"] if s["stop_type"] == "PICKUP")
    drop = next(s for s in assigned.json()["stops"] if s["stop_type"] == "DROP")
    await client.post(
        f"/api/v1/deliveries/{delivery_id}/stops/{pickup['id']}/complete",
        headers=headers,
        json={"proof": {"otp": "4321"}},
    )
    done = await client.post(
        f"/api/v1/deliveries/{delivery_id}/stops/{drop['id']}/complete",
        headers=headers,
        json={"proof": {"photo_url": "https://cdn.example/food-pod.jpg"}},
    )
    assert done.status_code == 200, done.text
    assert done.json()["status"] == "COMPLETED"

    ful = await client.get(f"/api/v1/orders/{order_id}/fulfillment", headers=headers)
    assert ful.json()["status"] == "COMPLETED"
    order_final = await client.get(f"/api/v1/orders/{order_id}", headers=headers)
    assert order_final.json()["status"] == "DELIVERED"

    # 7) Settlements from ledger
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

    platform_s = await client.post(
        "/api/v1/settlements",
        headers=headers,
        json={"party_type": "PLATFORM", "party_id": tenant_id, **period},
    )
    calc_p = await client.post(
        f"/api/v1/settlements/{platform_s.json()['id']}/calculate", headers=headers
    )
    assert calc_p.status_code == 200
    assert calc_p.json()["total_paise"] > 0

    # 8) Order debugger chain
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
    assert body["settlements"]
    assert "order" in body["chain"] and "settlements" in body["chain"]
