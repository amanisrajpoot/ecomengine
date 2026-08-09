"""Phase 10: settlements from ledger aggregation."""

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


async def _cod_order_with_business(client: AsyncClient, slug: str):
    headers = await _admin_headers(client)
    tenant = await client.post(
        "/api/v1/tenants", headers=headers, json={"name": slug, "slug": slug}
    )
    tenant_id = tenant.json()["id"]
    headers["X-Tenant-ID"] = tenant_id
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
        json={"cart_id": cart.json()["id"], "payment_provider": "cod"},
    )
    assert checkout.status_code == 200, checkout.text
    return headers, tenant_id, business_id, checkout.json()


def _period() -> dict[str, str]:
    start = datetime.now(UTC) - timedelta(days=1)
    end = datetime.now(UTC) + timedelta(days=1)
    return {"period_start": start.isoformat(), "period_end": end.isoformat()}


@pytest.mark.asyncio
async def test_merchant_settlement_lifecycle(client: AsyncClient) -> None:
    headers, tenant_id, business_id, order = await _cod_order_with_business(
        client, "settle-merchant"
    )
    period = _period()

    created = await client.post(
        "/api/v1/settlements",
        headers=headers,
        json={
            "party_type": "MERCHANT",
            "party_id": business_id,
            **period,
        },
    )
    assert created.status_code == 200, created.text
    assert created.json()["status"] == "PENDING"
    settlement_id = created.json()["id"]

    calculated = await client.post(
        f"/api/v1/settlements/{settlement_id}/calculate", headers=headers
    )
    assert calculated.status_code == 200, calculated.text
    body = calculated.json()
    assert body["status"] == "CALCULATED"
    assert body["total_paise"] > 0
    assert body["ledger_entry_ids"]
    assert body["report"]["calculated"]["entry_count"] >= 1

    reconciled = await client.post(
        f"/api/v1/settlements/{settlement_id}/reconcile", headers=headers
    )
    assert reconciled.status_code == 200, reconciled.text
    assert reconciled.json()["status"] == "RECONCILED"
    assert "reconcile" in reconciled.json()["report"]
    assert reconciled.json()["report"]["reconcile"]["matched"] is True

    approved = await client.post(
        f"/api/v1/settlements/{settlement_id}/approve",
        headers=headers,
        json={"reason": "ok"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "APPROVED"

    paid = await client.post(
        f"/api/v1/settlements/{settlement_id}/mark-paid",
        headers=headers,
        json={"reason": "payout_done"},
    )
    assert paid.status_code == 200
    assert paid.json()["status"] == "PAID"

    # Terminal — cannot approve again.
    bad = await client.post(
        f"/api/v1/settlements/{settlement_id}/approve", headers=headers, json={}
    )
    assert bad.status_code == 409

    order_settlements = await client.get(
        f"/api/v1/orders/{order['id']}/settlements", headers=headers
    )
    assert order_settlements.status_code == 200
    assert any(s["id"] == settlement_id for s in order_settlements.json())


@pytest.mark.asyncio
async def test_ledger_entry_not_double_settled(client: AsyncClient) -> None:
    headers, _tenant_id, business_id, _order = await _cod_order_with_business(
        client, "settle-dedupe"
    )
    period = _period()

    first = await client.post(
        "/api/v1/settlements",
        headers=headers,
        json={"party_type": "MERCHANT", "party_id": business_id, **period},
    )
    first_id = first.json()["id"]
    calc1 = await client.post(f"/api/v1/settlements/{first_id}/calculate", headers=headers)
    assert calc1.json()["total_paise"] > 0

    second = await client.post(
        "/api/v1/settlements",
        headers=headers,
        json={"party_type": "MERCHANT", "party_id": business_id, **period},
    )
    second_id = second.json()["id"]
    calc2 = await client.post(f"/api/v1/settlements/{second_id}/calculate", headers=headers)
    assert calc2.status_code == 200
    assert calc2.json()["total_paise"] == 0
    assert calc2.json()["report"]["calculated"]["skipped_already_settled"] >= 1


@pytest.mark.asyncio
async def test_platform_and_rider_settlements(client: AsyncClient) -> None:
    headers, tenant_id, _business_id, _order = await _cod_order_with_business(
        client, "settle-platform"
    )
    period = _period()

    platform = await client.post(
        "/api/v1/settlements",
        headers=headers,
        json={"party_type": "PLATFORM", "party_id": tenant_id, **period},
    )
    assert platform.status_code == 200, platform.text
    calc_p = await client.post(
        f"/api/v1/settlements/{platform.json()['id']}/calculate", headers=headers
    )
    assert calc_p.status_code == 200, calc_p.text
    assert calc_p.json()["total_paise"] > 0  # commission + platform fee

    rider_party = "00000000-0000-4000-8000-000000000099"
    rider = await client.post(
        "/api/v1/settlements",
        headers=headers,
        json={"party_type": "RIDER", "party_id": rider_party, **period},
    )
    assert rider.status_code == 200
    calc_r = await client.post(
        f"/api/v1/settlements/{rider.json()['id']}/calculate", headers=headers
    )
    assert calc_r.status_code == 200
    # Delivery fee accrued to RIDER_PAYABLE on COD capture.
    assert calc_r.json()["total_paise"] == 3000


@pytest.mark.asyncio
async def test_illegal_period_rejected(client: AsyncClient) -> None:
    headers = await _admin_headers(client)
    tenant = await client.post(
        "/api/v1/tenants",
        headers=headers,
        json={"name": "settle-bad-period", "slug": "settle-bad-period"},
    )
    headers["X-Tenant-ID"] = tenant.json()["id"]
    now = datetime.now(UTC)
    bad = await client.post(
        "/api/v1/settlements",
        headers=headers,
        json={
            "party_type": "PLATFORM",
            "party_id": tenant.json()["id"],
            "period_start": now.isoformat(),
            "period_end": (now - timedelta(hours=1)).isoformat(),
        },
    )
    assert bad.status_code == 400
    assert bad.json()["error"]["code"] == "INVALID_SETTLEMENT_PERIOD"
