"""Phase 10: settlements aggregated from ledger entries."""

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
    client: AsyncClient, headers: dict[str, str], slug: str
) -> tuple[str, str]:
    admin = await _admin_headers(client, headers["X-Tenant-ID"])
    biz = await client.post(
        "/api/v1/businesses",
        headers=admin,
        json={"name": f"Settle {slug}", "type": "FOOD", "status": "ACTIVE"},
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
        json={"name": "Full", "base_price_paise": 25000},
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
        json={"cart_id": cart_id},
    )
    assert order.status_code == 200, order.text
    return order.json()["id"], business_id


def _settlement_period() -> dict[str, str]:
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=1)).isoformat()
    end = (now + timedelta(days=1)).isoformat()
    return {"period_start": start, "period_end": end}


@pytest.mark.asyncio
async def test_merchant_settlement_from_ledger(client: AsyncClient) -> None:
    headers = await _tenant_and_customer(client, "p10-merchant")
    admin = await _admin_headers(client, headers["X-Tenant-ID"])
    order_id, business_id = await _checkout_order(client, headers, "merch")

    pay = await client.post(
        f"/api/v1/orders/{order_id}/payments",
        headers={**headers, "Idempotency-Key": "p10-pay"},
        json={"provider": "COD"},
    )
    assert pay.status_code == 200, pay.text

    ledger = await client.get(f"/api/v1/orders/{order_id}/ledger-entries", headers=admin)
    merchant_line = next(
        e
        for e in ledger.json()[0]["entries"]
        if e["account"] == "MERCHANT_PAYABLE"
    )
    expected_merchant = merchant_line["amount_paise"]

    calc = await client.post(
        "/api/v1/settlements/calculate",
        headers=admin,
        json={
            "party_type": "MERCHANT",
            "party_id": business_id,
            **(_settlement_period()),
        },
    )
    assert calc.status_code == 200, calc.text
    settlement = calc.json()
    assert settlement["status"] == "CALCULATED"
    assert settlement["party_type"] == "MERCHANT"
    assert settlement["total_paise"] == expected_merchant

    detail = await client.get(
        f"/api/v1/settlements/{settlement['id']}",
        headers=admin,
    )
    assert detail.status_code == 200, detail.text
    assert len(detail.json()["ledger_entry_ids"]) >= 1

    order_settlements = await client.get(
        f"/api/v1/orders/{order_id}/settlements",
        headers=admin,
    )
    assert order_settlements.status_code == 200
    assert any(s["id"] == settlement["id"] for s in order_settlements.json())


@pytest.mark.asyncio
async def test_settlement_lifecycle_transitions(client: AsyncClient) -> None:
    headers = await _tenant_and_customer(client, "p10-life")
    admin = await _admin_headers(client, headers["X-Tenant-ID"])
    order_id, business_id = await _checkout_order(client, headers, "life")

    await client.post(
        f"/api/v1/orders/{order_id}/payments",
        headers={**headers, "Idempotency-Key": "p10-life-pay"},
        json={"provider": "COD"},
    )

    calc = await client.post(
        "/api/v1/settlements/calculate",
        headers=admin,
        json={
            "party_type": "MERCHANT",
            "party_id": business_id,
            **(_settlement_period()),
        },
    )
    settlement_id = calc.json()["id"]

    for status in ("RECONCILED", "APPROVED", "PAID"):
        transition = await client.post(
            f"/api/v1/settlements/{settlement_id}/transition",
            headers=admin,
            json={"to_status": status, "reason": f"move to {status}"},
        )
        assert transition.status_code == 200, transition.text
        assert transition.json()["status"] == status


@pytest.mark.asyncio
async def test_platform_settlement_aggregates_revenue(client: AsyncClient) -> None:
    headers = await _tenant_and_customer(client, "p10-platform")
    admin = await _admin_headers(client, headers["X-Tenant-ID"])
    tenant_id = headers["X-Tenant-ID"]
    order_id, _ = await _checkout_order(client, headers, "plat")

    await client.post(
        f"/api/v1/orders/{order_id}/payments",
        headers={**headers, "Idempotency-Key": "p10-plat-pay"},
        json={"provider": "COD"},
    )

    ledger = await client.get(f"/api/v1/orders/{order_id}/ledger-entries", headers=admin)
    platform_line = next(
        e for e in ledger.json()[0]["entries"] if e["account"] == "PLATFORM_REVENUE"
    )

    calc = await client.post(
        "/api/v1/settlements/calculate",
        headers=admin,
        json={
            "party_type": "PLATFORM",
            "party_id": tenant_id,
            **(_settlement_period()),
        },
    )
    assert calc.status_code == 200, calc.text
    assert calc.json()["total_paise"] == platform_line["amount_paise"]
