"""Phase 13: Food golden path — full engine wiring (no FoodOrder table)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

PICKUP_ADDR = {
    "line1": "42 Spice Lane",
    "city": "Bengaluru",
    "state": "KA",
    "pincode": "560001",
}
DROP_ADDR = {
    "line1": "15 Customer Block",
    "city": "Bengaluru",
    "state": "KA",
    "pincode": "560034",
}
PICKUP_LAT, PICKUP_LNG = 12.9716, 77.5946
DROP_LAT, DROP_LNG = 12.9750, 77.6000


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
        json={"email": f"{slug}-rider@food.example.com", "password": "RiderPass123!"},
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


async def _food_menu_with_addons(
    client: AsyncClient, tenant_id: str, slug: str
) -> tuple[str, str, str]:
    admin = await _admin_headers(client, tenant_id)
    biz = await client.post(
        "/api/v1/businesses",
        headers=admin,
        json={"name": f"Golden Kitchen {slug}", "type": "FOOD", "status": "ACTIVE"},
    )
    assert biz.status_code == 200, biz.text
    business_id = biz.json()["id"]

    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=admin,
        json={"name": "Paneer Tikka"},
    )
    product_id = product.json()["id"]

    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product_id}/variants",
        headers=admin,
        json={"name": "Full", "base_price_paise": 18000},
    )
    variant_id = variant.json()["id"]

    addon = await client.post(
        f"/api/v1/businesses/{business_id}/addons",
        headers=admin,
        json={"name": "Extra Butter", "price_paise": 2000},
    )
    addon_id = addon.json()["id"]

    link = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product_id}/addon-links",
        headers=admin,
        json={"addon_id": addon_id},
    )
    assert link.status_code == 200, link.text

    return business_id, variant_id, addon_id


def _settlement_period() -> dict[str, str]:
    now = datetime.now(timezone.utc)
    return {
        "period_start": (now - timedelta(days=1)).isoformat(),
        "period_end": (now + timedelta(days=1)).isoformat(),
    }


async def _transition_order(
    client: AsyncClient,
    headers: dict[str, str],
    order_id: str,
    to_status: str,
) -> None:
    resp = await client.post(
        f"/api/v1/orders/{order_id}/transition",
        headers=headers,
        json={"to_status": to_status},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == to_status


@pytest.mark.asyncio
async def test_food_golden_path_to_settlement(client: AsyncClient) -> None:
    """Food: catalog+addons → cart → pay → kitchen → rider → ledger → settlement."""
    headers = await _tenant_and_customer(client, "p13-golden")
    tenant_id = headers["X-Tenant-ID"]
    admin = await _admin_headers(client, tenant_id)

    business_id, variant_id, addon_id = await _food_menu_with_addons(client, tenant_id, "golden")

    cart = await client.post(
        "/api/v1/carts",
        headers=headers,
        json={"business_id": business_id},
    )
    cart_id = cart.json()["id"]
    await client.post(
        f"/api/v1/carts/{cart_id}/items",
        headers=headers,
        json={
            "variant_id": variant_id,
            "quantity": 2,
            "addons": [{"addon_id": addon_id, "quantity": 1}],
        },
    )

    priced = await client.post(f"/api/v1/carts/{cart_id}/price", headers=headers)
    pricing = priced.json()["pricing"]
    assert pricing["subtotal_paise"] == 40000
    assert pricing["total_paise"] == 45650

    checkout = await client.post(
        "/api/v1/orders/checkout",
        headers=headers,
        json={"cart_id": cart_id, "fulfillment_type": "DELIVERY"},
    )
    assert checkout.status_code == 200, checkout.text
    order_id = checkout.json()["id"]
    assert checkout.json()["state_machine_profile"] == "FOOD_DELIVERY"
    assert checkout.json()["status"] == "PAYMENT_PENDING"

    fulfillment = await client.get(f"/api/v1/orders/{order_id}/fulfillment", headers=headers)
    assert fulfillment.json()["type"] == "DELIVERY"
    assert fulfillment.json()["status"] == "PENDING"
    fulfillment_id = fulfillment.json()["id"]

    pay = await client.post(
        f"/api/v1/orders/{order_id}/payments",
        headers={**headers, "Idempotency-Key": "p13-golden-pay"},
        json={"provider": "COD"},
    )
    assert pay.status_code == 200, pay.text
    assert pay.json()["status"] == "CAPTURED"

    order = await client.get(f"/api/v1/orders/{order_id}", headers=headers)
    assert order.json()["status"] == "PAYMENT_CONFIRMED"

    ledger = await client.get(f"/api/v1/orders/{order_id}/ledger-entries", headers=admin)
    capture_group = ledger.json()[0]
    debits = sum(e["amount_paise"] for e in capture_group["entries"] if e["direction"] == "DEBIT")
    credits = sum(e["amount_paise"] for e in capture_group["entries"] if e["direction"] == "CREDIT")
    assert debits == credits == pricing["total_paise"]

    merchant_line = next(
        e for e in capture_group["entries"] if e["account"] == "MERCHANT_PAYABLE"
    )
    expected_merchant = pricing["subtotal_paise"] - pricing.get("discount_paise", 0)

    for status in ("ACCEPTED", "PREPARING", "READY"):
        await _transition_order(client, admin, order_id, status)

    rider = await _register_rider(client, tenant_id, "p13-golden")
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
                    "contact": {"name": "Kitchen"},
                },
                {
                    "sequence": 1,
                    "stop_type": "DROP",
                    "address": DROP_ADDR,
                    "lat": DROP_LAT,
                    "lng": DROP_LNG,
                    "contact": {"name": "Customer"},
                },
            ],
        },
    )
    assert delivery.status_code == 200, delivery.text
    assert delivery.json()["status"] == "ASSIGNED"
    delivery_id = delivery.json()["id"]
    stops = delivery.json()["stops"]
    pickup_id = next(s["id"] for s in stops if s["stop_type"] == "PICKUP")
    drop_id = next(s["id"] for s in stops if s["stop_type"] == "DROP")

    await _transition_order(client, rider, order_id, "PICKED_UP")

    pickup_done = await client.post(
        f"/api/v1/deliveries/{delivery_id}/stops/{pickup_id}/complete",
        headers=rider,
        json={"proof": {"type": "OTP", "code": "4321"}},
    )
    assert pickup_done.json()["status"] == "IN_PROGRESS"

    await _transition_order(client, rider, order_id, "OUT_FOR_DELIVERY")

    drop_done = await client.post(
        f"/api/v1/deliveries/{delivery_id}/stops/{drop_id}/complete",
        headers=rider,
        json={"proof": {"type": "PHOTO", "url": "s3://pod/food.jpg"}},
    )
    assert drop_done.json()["status"] == "COMPLETED"

    await _transition_order(client, rider, order_id, "DELIVERED")

    final = await client.get(f"/api/v1/orders/{order_id}", headers=headers)
    assert final.json()["status"] == "DELIVERED"

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
    assert merchant_settlement.json()["total_paise"] == expected_merchant
    assert merchant_settlement.json()["status"] == "CALCULATED"

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
    platform_rev = pricing["platform_fee_paise"] + pricing.get("other_fees_paise", 0)
    assert platform_settlement.json()["total_paise"] == platform_rev

    order_settlements = await client.get(f"/api/v1/orders/{order_id}/settlements", headers=admin)
    settlement_ids = {s["id"] for s in order_settlements.json()}
    assert merchant_settlement.json()["id"] in settlement_ids
    assert platform_settlement.json()["id"] in settlement_ids


@pytest.mark.asyncio
async def test_food_profile_and_fulfillment_type(client: AsyncClient) -> None:
    headers = await _tenant_and_customer(client, "p13-profile")
    tenant_id = headers["X-Tenant-ID"]
    business_id, variant_id, addon_id = await _food_menu_with_addons(client, tenant_id, "prof")

    cart = await client.post(
        "/api/v1/carts",
        headers=headers,
        json={"business_id": business_id},
    )
    cart_id = cart.json()["id"]
    await client.post(
        f"/api/v1/carts/{cart_id}/items",
        headers=headers,
        json={
            "variant_id": variant_id,
            "quantity": 1,
            "addons": [{"addon_id": addon_id, "quantity": 1}],
        },
    )

    order = await client.post(
        "/api/v1/orders/checkout",
        headers=headers,
        json={"cart_id": cart_id, "fulfillment_type": "DELIVERY"},
    )
    assert order.json()["state_machine_profile"] == "FOOD_DELIVERY"
    assert order.json()["fulfillment_type"] == "DELIVERY"

    fulfillment = await client.get(
        f"/api/v1/orders/{order.json()['id']}/fulfillment",
        headers=headers,
    )
    assert fulfillment.json()["type"] == "DELIVERY"
