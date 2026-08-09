"""Phase 39: customer-scoped delivery tracking and fulfillment access."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _admin_headers(client: AsyncClient) -> dict[str, str]:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _customer_headers(client: AsyncClient, tenant_id: str, email: str) -> dict[str, str]:
    registered = await client.post(
        "/api/v1/auth/register",
        headers={"X-Tenant-ID": tenant_id},
        json={"email": email, "password": "Customer123!", "display_name": "Cust"},
    )
    assert registered.status_code == 200, registered.text
    return {
        "Authorization": f"Bearer {registered.json()['access_token']}",
        "X-Tenant-ID": tenant_id,
    }


async def _order_with_delivery(
    client: AsyncClient,
    admin: dict[str, str],
    customer: dict[str, str],
    rider_user_id: str,
) -> tuple[str, str]:
    biz = await client.post(
        "/api/v1/businesses",
        headers=admin,
        json={"name": "Track Kitchen", "type": "FOOD", "status": "ACTIVE"},
    )
    business_id = biz.json()["id"]
    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=admin,
        json={"name": "Meal"},
    )
    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product.json()['id']}/variants",
        headers=admin,
        json={"name": "Box", "base_price_paise": 12000},
    )
    cart = await client.post(
        "/api/v1/carts",
        headers=customer,
        json={"business_id": business_id, "delivery_fee_paise": 3000},
    )
    await client.post(
        f"/api/v1/carts/{cart.json()['id']}/items",
        headers=customer,
        json={"variant_id": variant.json()["id"], "quantity": 1},
    )
    checkout = await client.post(
        "/api/v1/orders/checkout",
        headers=customer,
        json={
            "cart_id": cart.json()["id"],
            "payment_provider": "cod",
            "customer_phone": "9876512345",
        },
    )
    assert checkout.status_code == 200, checkout.text
    order_id = checkout.json()["id"]

    partner = await client.post(
        "/api/v1/delivery-partners",
        headers=admin,
        json={"user_id": rider_user_id, "display_name": "Alex Rider"},
    )
    partner_id = partner.json()["id"]
    await client.post(
        f"/api/v1/delivery-partners/{partner_id}/location",
        headers=admin,
        json={"lat": 12.936, "lng": 77.625, "is_online": True},
    )
    for to_status, actor in (
        ("ACCEPTED", "merchant"),
        ("PREPARING", "merchant"),
        ("READY", "merchant"),
    ):
        await client.post(
            f"/api/v1/orders/{order_id}/transitions",
            headers=admin,
            json={"to_status": to_status, "actor": actor},
        )
    ful = await client.get(f"/api/v1/orders/{order_id}/fulfillment", headers=admin)
    delivery = await client.post(
        f"/api/v1/fulfillments/{ful.json()['id']}/deliveries",
        headers=admin,
        json={},
    )
    assigned = await client.post(
        f"/api/v1/deliveries/{delivery.json()['id']}/assign",
        headers=admin,
        json={"partner_id": partner_id},
    )
    assert assigned.status_code == 200, assigned.text
    await client.post(
        f"/api/v1/deliveries/{delivery.json()['id']}/tracking",
        headers=admin,
        json={"lat": 12.937, "lng": 77.626, "heading": 90.0},
    )
    return order_id, delivery.json()["id"]


@pytest.mark.asyncio
async def test_customer_gets_scoped_delivery_tracking(client: AsyncClient) -> None:
    admin = await _admin_headers(client)
    tenant = await client.post(
        "/api/v1/tenants",
        headers=admin,
        json={"name": "p39-track", "slug": "p39-track"},
    )
    tenant_id = tenant.json()["id"]
    admin["X-Tenant-ID"] = tenant_id

    cust = await _customer_headers(client, tenant_id, "track-cust@example.com")
    rider_reg = await client.post(
        "/api/v1/auth/register",
        headers={"X-Tenant-ID": tenant_id},
        json={"email": "track-rider@example.com", "password": "Rider123!", "display_name": "R"},
    )
    rider_user_id = rider_reg.json()["user_id"]
    assign = await client.post(
        f"/api/v1/users/{rider_user_id}/roles",
        headers=admin,
        json={"role": "DELIVERY_PARTNER", "tenant_id": tenant_id},
    )
    assert assign.status_code == 200, assign.text

    order_id, _ = await _order_with_delivery(client, admin, cust, rider_user_id)

    tracking = await client.get(f"/api/v1/orders/{order_id}/delivery", headers=cust)
    assert tracking.status_code == 200, tracking.text
    body = tracking.json()
    assert body["status"] == "ASSIGNED"
    assert body["partner"]["display_name"] == "Alex Rider"
    assert body["last_location"]["lat"] == 12.937
    assert len(body["stops"]) >= 1


@pytest.mark.asyncio
async def test_customer_cannot_read_other_order_delivery(client: AsyncClient) -> None:
    admin = await _admin_headers(client)
    tenant = await client.post(
        "/api/v1/tenants",
        headers=admin,
        json={"name": "p39-scope", "slug": "p39-scope"},
    )
    tenant_id = tenant.json()["id"]
    admin["X-Tenant-ID"] = tenant_id

    cust_a = await _customer_headers(client, tenant_id, "track-a@example.com")
    cust_b = await _customer_headers(client, tenant_id, "track-b@example.com")

    rider_reg = await client.post(
        "/api/v1/auth/register",
        headers={"X-Tenant-ID": tenant_id},
        json={"email": "scope-rider@example.com", "password": "Rider123!", "display_name": "R"},
    )
    rider_user_id = rider_reg.json()["user_id"]
    await client.post(
        f"/api/v1/users/{rider_user_id}/roles",
        headers=admin,
        json={"role": "DELIVERY_PARTNER", "tenant_id": tenant_id},
    )

    order_id, _ = await _order_with_delivery(client, admin, cust_a, rider_user_id)

    denied = await client.get(f"/api/v1/orders/{order_id}/delivery", headers=cust_b)
    assert denied.status_code == 404, denied.text

    denied_ful = await client.get(f"/api/v1/orders/{order_id}/fulfillment", headers=cust_b)
    assert denied_ful.status_code == 404, denied_ful.text
