"""Phase 11: fulfillment decoupled from orders."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient


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


async def _checkout_order(
    client: AsyncClient,
    headers: dict[str, str],
    slug: str,
    fulfillment_type: str = "DELIVERY",
) -> tuple[str, str]:
    admin = await _admin_headers(client, headers["X-Tenant-ID"])
    biz = await client.post(
        "/api/v1/businesses",
        headers=admin,
        json={"name": f"Fulfill {slug}", "type": "FOOD", "status": "ACTIVE"},
    )
    business_id = biz.json()["id"]
    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=admin,
        json={"name": "Biryani"},
    )
    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product.json()['id']}/variants",
        headers=admin,
        json={"name": "Full", "base_price_paise": 20000},
    )
    cart = await client.post(
        "/api/v1/carts",
        headers=headers,
        json={"business_id": business_id},
    )
    cart_id = cart.json()["id"]
    await client.post(
        f"/api/v1/carts/{cart_id}/items",
        headers=headers,
        json={"variant_id": variant.json()["id"], "quantity": 1},
    )
    order = await client.post(
        "/api/v1/orders/checkout",
        headers=headers,
        json={"cart_id": cart_id, "fulfillment_type": fulfillment_type},
    )
    assert order.status_code == 200, order.text
    return order.json()["id"], business_id


@pytest.mark.asyncio
async def test_checkout_creates_fulfillment(client: AsyncClient) -> None:
    headers = await _tenant_and_customer(client, "p11-create")
    order_id, _ = await _checkout_order(client, headers, "create", "DELIVERY")

    fulfillment = await client.get(
        f"/api/v1/orders/{order_id}/fulfillment",
        headers=headers,
    )
    assert fulfillment.status_code == 200, fulfillment.text
    body = fulfillment.json()
    assert body["order_id"] == order_id
    assert body["type"] == "DELIVERY"
    assert body["status"] == "PENDING"


@pytest.mark.asyncio
async def test_fulfillment_lifecycle(client: AsyncClient) -> None:
    headers = await _tenant_and_customer(client, "p11-life")
    admin = await _admin_headers(client, headers["X-Tenant-ID"])
    order_id, business_id = await _checkout_order(client, headers, "life")

    fulfillment = await client.get(f"/api/v1/orders/{order_id}/fulfillment", headers=admin)
    fulfillment_id = fulfillment.json()["id"]

    active = await client.post(
        f"/api/v1/fulfillments/{fulfillment_id}/transition",
        headers=admin,
        json={"to_status": "ACTIVE", "reason": "start prep"},
    )
    assert active.status_code == 200, active.text
    assert active.json()["status"] == "ACTIVE"

    completed = await client.post(
        f"/api/v1/fulfillments/{fulfillment_id}/transition",
        headers=admin,
        json={"to_status": "COMPLETED", "reason": "delivered"},
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "COMPLETED"

    listed = await client.get(
        f"/api/v1/fulfillments?business_id={business_id}&status=COMPLETED",
        headers=admin,
    )
    assert listed.status_code == 200
    assert any(f["id"] == fulfillment_id for f in listed.json())


@pytest.mark.asyncio
async def test_scheduled_fulfillment_type(client: AsyncClient) -> None:
    headers = await _tenant_and_customer(client, "p11-sched")
    admin = await _admin_headers(client, headers["X-Tenant-ID"])
    order_id, _ = await _checkout_order(client, headers, "sched", "SCHEDULED")

    fulfillment = await client.get(f"/api/v1/orders/{order_id}/fulfillment", headers=admin)
    fulfillment_id = fulfillment.json()["id"]
    assert fulfillment.json()["type"] == "SCHEDULED"

    scheduled_for = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    active = await client.post(
        f"/api/v1/fulfillments/{fulfillment_id}/transition",
        headers=admin,
        json={
            "to_status": "ACTIVE",
            "scheduled_for": scheduled_for,
            "reason": "scheduled slot",
        },
    )
    assert active.status_code == 200, active.text
    assert active.json()["scheduled_for"] is not None
