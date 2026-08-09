"""Phase 27: settlements UI — merchant-scoped reads."""

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


def _period() -> dict[str, str]:
    start = datetime.now(UTC) - timedelta(days=1)
    end = datetime.now(UTC) + timedelta(days=1)
    return {"period_start": start.isoformat(), "period_end": end.isoformat()}


async def _business(client: AsyncClient, headers: dict[str, str], name: str) -> str:
    biz = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={"name": name, "type": "FOOD", "status": "ACTIVE"},
    )
    assert biz.status_code == 200, biz.text
    return biz.json()["id"]


async def _merchant_headers(
    client: AsyncClient, tenant_id: str, email: str, business_id: str
) -> dict[str, str]:
    registered = await client.post(
        "/api/v1/auth/register",
        headers={"X-Tenant-ID": tenant_id},
        json={"email": email, "password": "Merchant123!", "display_name": "Owner"},
    )
    assert registered.status_code == 200, registered.text
    user_id = registered.json()["user_id"]
    admin = await _admin_headers(client)
    admin["X-Tenant-ID"] = tenant_id
    assign = await client.post(
        f"/api/v1/users/{user_id}/roles",
        headers=admin,
        json={
            "role": "BUSINESS_OWNER",
            "tenant_id": tenant_id,
            "business_id": business_id,
        },
    )
    assert assign.status_code == 200, assign.text
    return {
        "Authorization": f"Bearer {registered.json()['access_token']}",
        "X-Tenant-ID": tenant_id,
    }


@pytest.mark.asyncio
async def test_merchant_sees_only_own_settlements(client: AsyncClient) -> None:
    admin = await _admin_headers(client)
    tenant = await client.post(
        "/api/v1/tenants",
        headers=admin,
        json={"name": "p27-settle", "slug": "p27-settle"},
    )
    tenant_id = tenant.json()["id"]
    admin["X-Tenant-ID"] = tenant_id

    biz_a = await _business(client, admin, "Kitchen A")
    biz_b = await _business(client, admin, "Kitchen B")
    period = _period()

    settle_a = await client.post(
        "/api/v1/settlements",
        headers=admin,
        json={"party_type": "MERCHANT", "party_id": biz_a, **period},
    )
    settle_b = await client.post(
        "/api/v1/settlements",
        headers=admin,
        json={"party_type": "MERCHANT", "party_id": biz_b, **period},
    )
    assert settle_a.status_code == 200, settle_a.text
    assert settle_b.status_code == 200, settle_b.text
    settlement_a_id = settle_a.json()["id"]

    merchant_a = await _merchant_headers(client, tenant_id, "owner-a@example.com", biz_a)

    listed = await client.get("/api/v1/settlements", headers=merchant_a)
    assert listed.status_code == 200, listed.text
    ids = {row["id"] for row in listed.json()}
    assert settlement_a_id in ids
    assert settle_b.json()["id"] not in ids

    peek_b = await client.get(
        f"/api/v1/settlements/{settle_b.json()['id']}", headers=merchant_a
    )
    assert peek_b.status_code == 404
