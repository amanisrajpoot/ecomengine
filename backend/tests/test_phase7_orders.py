"""Phase 7: universal orders + configurable state machines."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.orders.states import registry


def test_state_machine_profiles_are_distinct() -> None:
    food = registry.get("FOOD_DELIVERY")
    hyper = registry.get("HYPERLOCAL_DELIVERY")
    courier = registry.get("COURIER")
    assert food.can_transition("ACCEPTED", "PREPARING", "merchant")
    assert not food.can_transition("ACCEPTED", "PICKING", "merchant")
    assert hyper.can_transition("ACCEPTED", "PICKING", "staff")
    assert courier.can_transition("PAYMENT_CONFIRMED", "PICKUP_ASSIGNED", "system")
    assert not courier.can_transition("PAYMENT_CONFIRMED", "ACCEPTED", "merchant")
    assert registry.profile_for_business_type("FOOD") == "FOOD_DELIVERY"
    assert registry.profile_for_business_type("GROCERY") == "HYPERLOCAL_DELIVERY"
    assert registry.profile_for_business_type("COURIER") == "COURIER"


def test_illegal_transition_raises() -> None:
    food = registry.get("FOOD_DELIVERY")
    with pytest.raises(Exception) as exc:
        food.assert_can_transition("CREATED", "DELIVERED", "rider")
    assert getattr(exc.value, "code", None) == "ORDER_ILLEGAL_TRANSITION"


async def _admin_headers(client: AsyncClient) -> dict[str, str]:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _food_cart(client: AsyncClient, slug: str):
    headers = await _admin_headers(client)
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
        json={"business_id": business_id, "delivery_fee_paise": 3000, "platform_fee_paise": 500},
    )
    cart_id = cart.json()["id"]
    await client.post(
        f"/api/v1/carts/{cart_id}/items",
        headers=headers,
        json={"variant_id": variant.json()["id"], "quantity": 1},
    )
    return headers, cart_id


@pytest.mark.asyncio
async def test_food_cod_checkout_and_happy_path(client: AsyncClient) -> None:
    headers, cart_id = await _food_cart(client, "order-food")
    checkout = await client.post(
        "/api/v1/orders/checkout",
        headers=headers,
        json={"cart_id": cart_id, "payment_method": "COD", "fulfillment_type": "DELIVERY"},
    )
    assert checkout.status_code == 200, checkout.text
    order = checkout.json()
    assert order["state_machine_profile"] == "FOOD_DELIVERY"
    assert order["status"] == "PAYMENT_CONFIRMED"
    assert order["pricing_snapshot"]["total_paise"] > 0
    assert len(order["items"]) == 1
    assert any(e["to_status"] == "PAYMENT_CONFIRMED" for e in order["status_events"])

    order_id = order["id"]

    async def move(to_status: str, actor: str) -> dict:
        resp = await client.post(
            f"/api/v1/orders/{order_id}/transitions",
            headers=headers,
            json={"to_status": to_status, "actor": actor},
        )
        assert resp.status_code == 200, resp.text
        return resp.json()

    await move("ACCEPTED", "merchant")
    await move("PREPARING", "merchant")
    await move("READY", "merchant")
    await move("PICKED_UP", "rider")
    await move("OUT_FOR_DELIVERY", "rider")
    delivered = await move("DELIVERED", "rider")
    assert delivered["status"] == "DELIVERED"

    illegal = await client.post(
        f"/api/v1/orders/{order_id}/transitions",
        headers=headers,
        json={"to_status": "ACCEPTED", "actor": "merchant"},
    )
    assert illegal.status_code == 409
    assert illegal.json()["error"]["code"] == "ORDER_ILLEGAL_TRANSITION"


@pytest.mark.asyncio
async def test_online_checkout_starts_payment_pending(client: AsyncClient) -> None:
    headers, cart_id = await _food_cart(client, "order-online")
    checkout = await client.post(
        "/api/v1/orders/checkout",
        headers=headers,
        json={"cart_id": cart_id, "payment_method": "ONLINE"},
    )
    assert checkout.status_code == 200, checkout.text
    assert checkout.json()["status"] == "PAYMENT_PENDING"
    order_id = checkout.json()["id"]

    payments = await client.get(f"/api/v1/orders/{order_id}/payments", headers=headers)
    assert payments.status_code == 200, payments.text
    assert payments.json()[0]["provider"] == "cashfree"

    confirmed = await client.post(
        f"/api/v1/orders/{order_id}/payments/verify",
        headers=headers,
        json={},
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["order_status"] == "PAYMENT_CONFIRMED"


@pytest.mark.asyncio
async def test_courier_profile_transitions(client: AsyncClient) -> None:
    headers = await _admin_headers(client)
    tenant = await client.post(
        "/api/v1/tenants",
        headers=headers,
        json={"name": "order-courier", "slug": "order-courier"},
    )
    headers["X-Tenant-ID"] = tenant.json()["id"]
    biz = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={
            "name": "Dash",
            "type": "COURIER",
            "status": "ACTIVE",
            "capabilities": {
                "catalog": True,
                "inventory": False,
                "addons": False,
                "delivery": True,
                "scheduledOrders": True,
            },
        },
    )
    business_id = biz.json()["id"]
    # Enable catalog temporarily for a priced line item.
    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=headers,
        json={"name": "Package"},
    )
    # COURIER defaults catalog false — override capabilities on create above.
    assert product.status_code == 200, product.text
    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product.json()['id']}/variants",
        headers=headers,
        json={"name": "Small", "base_price_paise": 9900},
    )
    cart = await client.post(
        "/api/v1/carts",
        headers=headers,
        json={"business_id": business_id, "delivery_fee_paise": 0, "platform_fee_paise": 0},
    )
    await client.post(
        f"/api/v1/carts/{cart.json()['id']}/items",
        headers=headers,
        json={"variant_id": variant.json()["id"], "quantity": 1},
    )
    checkout = await client.post(
        "/api/v1/orders/checkout",
        headers=headers,
        json={"cart_id": cart.json()["id"], "payment_method": "COD"},
    )
    assert checkout.status_code == 200, checkout.text
    assert checkout.json()["state_machine_profile"] == "COURIER"
    order_id = checkout.json()["id"]
    assert checkout.json()["status"] == "PAYMENT_CONFIRMED"

    assigned = await client.post(
        f"/api/v1/orders/{order_id}/transitions",
        headers=headers,
        json={"to_status": "PICKUP_ASSIGNED", "actor": "system"},
    )
    assert assigned.status_code == 200
    # Food-only state must fail on courier profile.
    bad = await client.post(
        f"/api/v1/orders/{order_id}/transitions",
        headers=headers,
        json={"to_status": "PREPARING", "actor": "merchant"},
    )
    assert bad.status_code == 409
