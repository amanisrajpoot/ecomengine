"""Phase 6: taxation and GST calculation."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _admin_headers(client: AsyncClient, tenant_id: str) -> dict[str, str]:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    return {
        "Authorization": f"Bearer {login.json()['access_token']}",
        "X-Tenant-ID": tenant_id,
    }


async def _tenant_id(client: AsyncClient, slug: str) -> str:
    admin_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
    tenant = await client.post(
        "/api/v1/tenants",
        headers=headers,
        json={"name": slug, "slug": slug},
    )
    return tenant.json()["id"]


@pytest.mark.asyncio
async def test_default_tax_rules_seeded(client: AsyncClient) -> None:
    tenant_id = await _tenant_id(client, "p6-rules")
    headers = await _admin_headers(client, tenant_id)

    rules = await client.get("/api/v1/tax-rules", headers=headers)
    assert rules.status_code == 200, rules.text
    codes = {r["code"] for r in rules.json()}
    assert "CGST" in codes and "SGST" in codes


@pytest.mark.asyncio
async def test_calculate_goods_cgst_sgst(client: AsyncClient) -> None:
    tenant_id = await _tenant_id(client, "p6-calc")
    headers = await _admin_headers(client, tenant_id)

    result = await client.post(
        "/api/v1/tax/calculate",
        headers=headers,
        json={"goods_taxable_paise": 50000, "delivery_taxable_paise": 0},
    )
    assert result.status_code == 200, result.text
    body = result.json()
    assert body["tax_paise"] == 2500  # 5% CGST+SGST on 50000
    assert len(body["lines"]) == 2
    assert sum(line["amount_paise"] for line in body["lines"]) == 2500


@pytest.mark.asyncio
async def test_calculate_includes_delivery_tax(client: AsyncClient) -> None:
    tenant_id = await _tenant_id(client, "p6-del")
    headers = await _admin_headers(client, tenant_id)

    result = await client.post(
        "/api/v1/tax/calculate",
        headers=headers,
        json={"goods_taxable_paise": 40000, "delivery_taxable_paise": 3000},
    )
    assert result.status_code == 200, result.text
    body = result.json()
    # CGST/SGST on goods: 2000, on delivery: 150
    assert body["tax_paise"] == 2150


@pytest.mark.asyncio
async def test_create_tenant_tax_rule(client: AsyncClient) -> None:
    tenant_id = await _tenant_id(client, "p6-create")
    headers = await _admin_headers(client, tenant_id)

    created = await client.post(
        "/api/v1/tax-rules",
        headers=headers,
        json={
            "code": "IGST",
            "category": "GOODS",
            "jurisdiction": "IN",
            "rate_bps": 500,
            "inclusive": False,
            "payer": "CUSTOMER",
            "kind": "CUSTOMER_TRANSACTION",
        },
    )
    assert created.status_code == 200, created.text
    assert created.json()["code"] == "IGST"
    assert created.json()["rate_bps"] == 500
