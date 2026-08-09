"""Phase 11: fulfillment decoupled from order (no rider fields on Order)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.fulfillment.states import registry


def test_fulfillment_machine_self_pickup_and_delivery() -> None:
    assert registry.can_transition("READY", "COMPLETED", "merchant", "SELF_PICKUP")
    assert registry.can_transition("READY", "AWAITING_PICKUP", "system", "DELIVERY")
    assert registry.can_transition("AWAITING_PICKUP", "IN_TRANSIT", "rider", "DELIVERY")
    assert not registry.can_transition("PENDING", "IN_TRANSIT", "rider", "DELIVERY")


async def _admin_headers(client: AsyncClient) -> dict[str, str]:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _cod_order(client: AsyncClient, slug: str, fulfillment_type: str = "DELIVERY"):
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
            "fulfillment_type": fulfillment_type,
        },
    )
    assert checkout.status_code == 200, checkout.text
    return headers, checkout.json()


@pytest.mark.asyncio
async def test_cod_creates_fulfillment_pending(client: AsyncClient) -> None:
    headers, order = await _cod_order(client, "ful-cod")
    assert order["status"] == "PAYMENT_CONFIRMED"

    fulfillment = await client.get(
        f"/api/v1/orders/{order['id']}/fulfillment", headers=headers
    )
    assert fulfillment.status_code == 200, fulfillment.text
    body = fulfillment.json()
    assert body["order_id"] == order["id"]
    assert body["type"] == "DELIVERY"
    assert body["status"] == "PENDING"
    assert body["status_events"]
    # No rider/partner fields on fulfillment itself.
    assert "partner_id" not in body
    assert "rider_id" not in body


@pytest.mark.asyncio
async def test_fulfillment_syncs_along_order_happy_path(client: AsyncClient) -> None:
    headers, order = await _cod_order(client, "ful-sync")
    order_id = order["id"]

    async def move(to_status: str, actor: str) -> None:
        resp = await client.post(
            f"/api/v1/orders/{order_id}/transitions",
            headers=headers,
            json={"to_status": to_status, "actor": actor},
        )
        assert resp.status_code == 200, resp.text

    await move("ACCEPTED", "merchant")
    ful = (await client.get(f"/api/v1/orders/{order_id}/fulfillment", headers=headers)).json()
    assert ful["status"] == "ACCEPTED"

    await move("PREPARING", "merchant")
    ful = (await client.get(f"/api/v1/orders/{order_id}/fulfillment", headers=headers)).json()
    assert ful["status"] == "PREPARING"

    await move("READY", "merchant")
    ful = (await client.get(f"/api/v1/orders/{order_id}/fulfillment", headers=headers)).json()
    assert ful["status"] == "READY"

    await move("PICKED_UP", "rider")
    ful = (await client.get(f"/api/v1/orders/{order_id}/fulfillment", headers=headers)).json()
    assert ful["status"] == "IN_TRANSIT"

    await move("OUT_FOR_DELIVERY", "rider")
    await move("DELIVERED", "rider")
    ful = (await client.get(f"/api/v1/orders/{order_id}/fulfillment", headers=headers)).json()
    assert ful["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_self_pickup_manual_complete(client: AsyncClient) -> None:
    headers, order = await _cod_order(client, "ful-pickup", fulfillment_type="SELF_PICKUP")
    ful = (await client.get(f"/api/v1/orders/{order['id']}/fulfillment", headers=headers)).json()
    assert ful["type"] == "SELF_PICKUP"

    await client.post(
        f"/api/v1/orders/{order['id']}/transitions",
        headers=headers,
        json={"to_status": "ACCEPTED", "actor": "merchant"},
    )
    await client.post(
        f"/api/v1/orders/{order['id']}/transitions",
        headers=headers,
        json={"to_status": "PREPARING", "actor": "merchant"},
    )
    await client.post(
        f"/api/v1/orders/{order['id']}/transitions",
        headers=headers,
        json={"to_status": "READY", "actor": "merchant"},
    )
    ful = (await client.get(f"/api/v1/orders/{order['id']}/fulfillment", headers=headers)).json()
    assert ful["status"] == "READY"

    done = await client.post(
        f"/api/v1/fulfillments/{ful['id']}/transitions",
        headers=headers,
        json={"to_status": "COMPLETED", "actor": "merchant", "reason": "customer_collected"},
    )
    assert done.status_code == 200, done.text
    assert done.json()["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_idempotent_create_and_illegal_transition(client: AsyncClient) -> None:
    headers, order = await _cod_order(client, "ful-idemp")
    first = await client.post(
        f"/api/v1/orders/{order['id']}/fulfillment", headers=headers, json={}
    )
    assert first.status_code == 200
    second = await client.post(
        f"/api/v1/orders/{order['id']}/fulfillment", headers=headers, json={}
    )
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]

    bad = await client.post(
        f"/api/v1/fulfillments/{first.json()['id']}/transitions",
        headers=headers,
        json={"to_status": "IN_TRANSIT", "actor": "rider"},
    )
    assert bad.status_code == 409
    assert bad.json()["error"]["code"] == "FULFILLMENT_ILLEGAL_TRANSITION"


@pytest.mark.asyncio
async def test_cashfree_pending_has_no_fulfillment_until_capture(client: AsyncClient) -> None:
    headers = await _admin_headers(client)
    tenant = await client.post(
        "/api/v1/tenants",
        headers=headers,
        json={"name": "ful-online", "slug": "ful-online"},
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
        json={"cart_id": cart.json()["id"], "payment_provider": "cashfree"},
    )
    assert checkout.status_code == 200
    order_id = checkout.json()["id"]
    missing = await client.get(f"/api/v1/orders/{order_id}/fulfillment", headers=headers)
    assert missing.status_code == 404

    payment = (await client.get(f"/api/v1/orders/{order_id}/payments", headers=headers)).json()[0]
    verify = await client.post(
        f"/api/v1/orders/{order_id}/payments/verify",
        headers=headers,
        json={"provider": "cashfree", "provider_ref": payment["provider_ref"]},
    )
    assert verify.status_code == 200
    ful = await client.get(f"/api/v1/orders/{order_id}/fulfillment", headers=headers)
    assert ful.status_code == 200
    assert ful.json()["status"] == "PENDING"
