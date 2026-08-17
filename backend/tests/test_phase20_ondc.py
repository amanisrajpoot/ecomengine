"""Phase 20: ONDC adapter search → select → init → confirm → status."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

ONDC_CONTEXT = {
    "domain": "ONDC:RET10",
    "city": "std:080",
    "country": "IND",
    "action": "search",
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
    customer_body = reg.json()
    return {
        "Authorization": f"Bearer {admin_login.json()['access_token']}",
        "X-Tenant-ID": tenant_id,
        "customer_id": customer_body["user_id"],
    }


async def _food_menu(
    client: AsyncClient, headers: dict[str, str], slug: str
) -> tuple[str, str]:
    business = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={"name": f"ONDC {slug}", "type": "FOOD", "status": "ACTIVE"},
    )
    business_id = business.json()["id"]
    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=headers,
        json={"name": "Thali"},
    )
    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product.json()['id']}/variants",
        headers=headers,
        json={"name": "Regular", "base_price_paise": 15000},
    )
    return business_id, variant.json()["id"]


@pytest.mark.asyncio
async def test_ondc_search_lists_catalog(client: AsyncClient) -> None:
    headers = await _tenant_and_customer(client, "p20-search")
    business_id, variant_id = await _food_menu(client, headers, "search")

    search = await client.post(
        "/api/v1/ondc/search",
        headers=headers,
        json={"context": ONDC_CONTEXT, "message": {"business_type": "FOOD"}},
    )
    assert search.status_code == 200, search.text
    body = search.json()
    assert body["context"]["action"] == "on_search"
    assert any(p["id"] == business_id for p in body["message"]["providers"])
    assert any(i["id"] == variant_id for i in body["message"]["items"])


@pytest.mark.asyncio
async def test_ondc_confirm_golden_path(client: AsyncClient) -> None:
    headers = await _tenant_and_customer(client, "p20-golden")
    business_id, variant_id = await _food_menu(client, headers, "golden")
    customer_id = headers["customer_id"]

    select = await client.post(
        "/api/v1/ondc/select",
        headers=headers,
        json={
            "context": {**ONDC_CONTEXT, "action": "select"},
            "message": {
                "customer_id": customer_id,
                "business_id": business_id,
                "items": [{"variant_id": variant_id, "quantity": 2}],
            },
        },
    )
    assert select.status_code == 200, select.text
    cart_id = select.json()["message"]["cart_id"]
    quote_total = select.json()["message"]["quote"]["total_paise"]
    assert quote_total > 0

    init = await client.post(
        "/api/v1/ondc/init",
        headers=headers,
        json={
            "context": {**ONDC_CONTEXT, "action": "init"},
            "message": {"customer_id": customer_id, "cart_id": cart_id},
        },
    )
    assert init.status_code == 200, init.text
    assert init.json()["message"]["payment"]["amount_paise"] == quote_total

    confirm = await client.post(
        "/api/v1/ondc/confirm",
        headers=headers,
        json={
            "context": {**ONDC_CONTEXT, "action": "confirm"},
            "message": {
                "customer_id": customer_id,
                "cart_id": cart_id,
                "fulfillment_type": "DELIVERY",
            },
        },
    )
    assert confirm.status_code == 200, confirm.text
    confirm_body = confirm.json()["message"]
    assert confirm_body["order_state"] == "PAYMENT_CONFIRMED"
    assert confirm_body["payment_status"] == "CAPTURED"
    order_id = confirm_body["order_id"]

    status = await client.post(
        "/api/v1/ondc/status",
        headers=headers,
        json={
            "context": {**ONDC_CONTEXT, "action": "status"},
            "message": {"order_id": order_id},
        },
    )
    assert status.status_code == 200, status.text
    assert status.json()["message"]["state"] == "PAYMENT_CONFIRMED"
    assert status.json()["context"]["action"] == "on_status"
