"""Phase 31: rider ops UI — notifications and settlements scoping."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient


async def _admin_headers(client: AsyncClient) -> dict[str, str]:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _rider_headers(client: AsyncClient, tenant_id: str, email: str) -> dict[str, str]:
    registered = await client.post(
        "/api/v1/auth/register",
        headers={"X-Tenant-ID": tenant_id},
        json={"email": email, "password": "Rider123!", "display_name": "Rider"},
    )
    assert registered.status_code == 200, registered.text
    user_id = registered.json()["user_id"]
    admin = await _admin_headers(client)
    admin["X-Tenant-ID"] = tenant_id
    assign = await client.post(
        f"/api/v1/users/{user_id}/roles",
        headers=admin,
        json={"role": "DELIVERY_PARTNER", "tenant_id": tenant_id},
    )
    assert assign.status_code == 200, assign.text
    return {
        "Authorization": f"Bearer {registered.json()['access_token']}",
        "X-Tenant-ID": tenant_id,
    }, user_id


def _period() -> dict[str, str]:
    start = datetime.now(UTC) - timedelta(days=1)
    end = datetime.now(UTC) + timedelta(days=1)
    return {"period_start": start.isoformat(), "period_end": end.isoformat()}


async def _food_order_with_delivery(
    client: AsyncClient, headers: dict[str, str], rider_user_id: str
) -> tuple[str, str]:
    biz = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={"name": "Rider Kitchen", "type": "FOOD", "status": "ACTIVE"},
    )
    business_id = biz.json()["id"]
    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=headers,
        json={"name": "Meal"},
    )
    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product.json()['id']}/variants",
        headers=headers,
        json={"name": "Box", "base_price_paise": 12000},
    )
    cart = await client.post(
        "/api/v1/carts",
        headers=headers,
        json={"business_id": business_id, "delivery_fee_paise": 3000},
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
            "customer_phone": "9876511111",
        },
    )
    assert checkout.status_code == 200, checkout.text
    order_id = checkout.json()["id"]

    partner = await client.post(
        "/api/v1/delivery-partners",
        headers=headers,
        json={"user_id": rider_user_id, "display_name": "Rider"},
    )
    partner_id = partner.json()["id"]
    await client.post(
        f"/api/v1/delivery-partners/{partner_id}/location",
        headers=headers,
        json={"lat": 12.936, "lng": 77.625, "is_online": True},
    )
    for to_status, actor in (
        ("ACCEPTED", "merchant"),
        ("PREPARING", "merchant"),
        ("READY", "merchant"),
    ):
        await client.post(
            f"/api/v1/orders/{order_id}/transitions",
            headers=headers,
            json={"to_status": to_status, "actor": actor},
        )
    ful = await client.get(f"/api/v1/orders/{order_id}/fulfillment", headers=headers)
    delivery = await client.post(
        f"/api/v1/fulfillments/{ful.json()['id']}/deliveries",
        headers=headers,
        json={},
    )
    assigned = await client.post(
        f"/api/v1/deliveries/{delivery.json()['id']}/assign",
        headers=headers,
        json={"partner_id": partner_id},
    )
    assert assigned.status_code == 200, assigned.text
    return order_id, partner_id


@pytest.mark.asyncio
async def test_rider_sees_notifications_for_assigned_orders_only(client: AsyncClient) -> None:
    admin = await _admin_headers(client)
    tenant = await client.post(
        "/api/v1/tenants",
        headers=admin,
        json={"name": "p31-rider-notify", "slug": "p31-rider-notify"},
    )
    tenant_id = tenant.json()["id"]
    admin["X-Tenant-ID"] = tenant_id

    rider_a, rider_a_user = await _rider_headers(client, tenant_id, "rider-a@example.com")
    rider_b, rider_b_user = await _rider_headers(client, tenant_id, "rider-b@example.com")

    order_a, _ = await _food_order_with_delivery(client, admin, rider_a_user)
    order_b, _ = await _food_order_with_delivery(client, admin, rider_b_user)

    notes_a = await client.get(
        "/api/v1/notifications",
        headers=rider_a,
        params={"order_id": order_a},
    )
    assert notes_a.status_code == 200, notes_a.text
    assert len(notes_a.json()) >= 1

    peek_b = await client.get(
        "/api/v1/notifications",
        headers=rider_a,
        params={"order_id": order_b},
    )
    assert peek_b.status_code == 200
    assert peek_b.json() == []


@pytest.mark.asyncio
async def test_rider_sees_only_own_settlements(client: AsyncClient) -> None:
    admin = await _admin_headers(client)
    tenant = await client.post(
        "/api/v1/tenants",
        headers=admin,
        json={"name": "p31-rider-settle", "slug": "p31-rider-settle"},
    )
    tenant_id = tenant.json()["id"]
    admin["X-Tenant-ID"] = tenant_id

    rider_a, rider_a_user = await _rider_headers(client, tenant_id, "settle-a@example.com")
    rider_b, rider_b_user = await _rider_headers(client, tenant_id, "settle-b@example.com")

    _, partner_a = await _food_order_with_delivery(client, admin, rider_a_user)
    _, partner_b = await _food_order_with_delivery(client, admin, rider_b_user)
    period = _period()

    settle_a = await client.post(
        "/api/v1/settlements",
        headers=admin,
        json={"party_type": "RIDER", "party_id": partner_a, **period},
    )
    assert settle_a.status_code == 200, settle_a.text
    await client.post(
        f"/api/v1/settlements/{settle_a.json()['id']}/calculate", headers=admin
    )

    settle_b = await client.post(
        "/api/v1/settlements",
        headers=admin,
        json={"party_type": "RIDER", "party_id": partner_b, **period},
    )
    assert settle_b.status_code == 200

    own = await client.get("/api/v1/settlements", headers=rider_a, params={"party_type": "RIDER"})
    assert own.status_code == 200
    ids = {s["id"] for s in own.json()}
    assert settle_a.json()["id"] in ids
    assert settle_b.json()["id"] not in ids

    peek = await client.get(
        f"/api/v1/settlements/{settle_b.json()['id']}", headers=rider_a
    )
    assert peek.status_code == 404
