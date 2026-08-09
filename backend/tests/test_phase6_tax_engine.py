"""Phase 6: independent TaxRule engine."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.taxation.engine import calculate_tax_from_rules
from app.taxation.schemas import TaxCategory, TaxKind


class _Rule:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_customer_vs_platform_vs_settlement_kinds_are_distinct() -> None:
    rules = [
        _Rule(
            code="CGST",
            category="GOODS",
            jurisdiction="IN-INTRA",
            rate_bps=250,
            inclusive=False,
            payer="CUSTOMER",
            kind="CUSTOMER_TRANSACTION",
        ),
        _Rule(
            code="SGST",
            category="GOODS",
            jurisdiction="IN-INTRA",
            rate_bps=250,
            inclusive=False,
            payer="CUSTOMER",
            kind="CUSTOMER_TRANSACTION",
        ),
        _Rule(
            code="CGST",
            category="COMMISSION",
            jurisdiction="IN-INTRA",
            rate_bps=900,
            inclusive=False,
            payer="MERCHANT",
            kind="PLATFORM_SERVICE",
        ),
        _Rule(
            code="SGST",
            category="COMMISSION",
            jurisdiction="IN-INTRA",
            rate_bps=900,
            inclusive=False,
            payer="MERCHANT",
            kind="PLATFORM_SERVICE",
        ),
        _Rule(
            code="CGST",
            category="COMMISSION",
            jurisdiction="IN-INTRA",
            rate_bps=900,
            inclusive=False,
            payer="MERCHANT",
            kind="SETTLEMENT_DEDUCTION",
        ),
    ]

    customer = calculate_tax_from_rules(
        taxable_paise=100_000,
        kind=TaxKind.CUSTOMER_TRANSACTION.value,
        category=TaxCategory.GOODS.value,
        jurisdiction="IN-INTRA",
        rules=rules,
    )
    assert customer.tax_paise == 5000
    assert {line.code for line in customer.lines} == {"CGST", "SGST"}
    assert all(line.kind == "CUSTOMER_TRANSACTION" for line in customer.lines)
    assert all(line.payer == "CUSTOMER" for line in customer.lines)

    platform = calculate_tax_from_rules(
        taxable_paise=10_000,
        kind=TaxKind.PLATFORM_SERVICE.value,
        category=TaxCategory.COMMISSION.value,
        jurisdiction="IN-INTRA",
        rules=rules,
    )
    assert platform.tax_paise == 1800
    assert all(line.kind == "PLATFORM_SERVICE" for line in platform.lines)
    assert all(line.payer == "MERCHANT" for line in platform.lines)

    settlement = calculate_tax_from_rules(
        taxable_paise=10_000,
        kind=TaxKind.SETTLEMENT_DEDUCTION.value,
        category=TaxCategory.COMMISSION.value,
        jurisdiction="IN-INTRA",
        rules=rules,
    )
    assert settlement.tax_paise == 900
    assert settlement.lines[0].kind == "SETTLEMENT_DEDUCTION"


@pytest.mark.asyncio
async def test_seeded_rules_and_calculate_api(client: AsyncClient) -> None:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    rules = await client.get("/api/v1/tax/rules", headers=headers)
    assert rules.status_code == 200, rules.text
    assert len(rules.json()) >= 5
    kinds = {r["kind"] for r in rules.json()}
    assert "CUSTOMER_TRANSACTION" in kinds
    assert "PLATFORM_SERVICE" in kinds
    assert "SETTLEMENT_DEDUCTION" in kinds
    # Never a blob "GST" code
    assert "GST" not in {r["code"] for r in rules.json()}

    calc = await client.post(
        "/api/v1/tax/calculate",
        headers=headers,
        json={
            "taxable_paise": 100000,
            "kind": "CUSTOMER_TRANSACTION",
            "category": "GOODS",
            "jurisdiction": "IN-INTRA",
        },
    )
    assert calc.status_code == 200, calc.text
    body = calc.json()
    assert body["tax_paise"] == 5000
    assert {line["code"] for line in body["lines"]} == {"CGST", "SGST"}

    commission = await client.post(
        "/api/v1/tax/calculate",
        headers=headers,
        json={
            "taxable_paise": 10000,
            "kind": "PLATFORM_SERVICE",
            "category": "COMMISSION",
            "jurisdiction": "IN-INTRA",
        },
    )
    assert commission.status_code == 200, commission.text
    assert commission.json()["tax_paise"] == 1800
    assert all(line["kind"] == "PLATFORM_SERVICE" for line in commission.json()["lines"])


@pytest.mark.asyncio
async def test_inter_state_igst_rule(client: AsyncClient) -> None:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    calc = await client.post(
        "/api/v1/tax/calculate",
        headers=headers,
        json={
            "taxable_paise": 20000,
            "kind": "CUSTOMER_TRANSACTION",
            "category": "GOODS",
            "jurisdiction": "IN-INTER",
        },
    )
    assert calc.status_code == 200, calc.text
    assert calc.json()["tax_paise"] == 1000
    assert len(calc.json()["lines"]) == 1
    assert calc.json()["lines"][0]["code"] == "IGST"


@pytest.mark.asyncio
async def test_create_custom_tenant_tax_rule(client: AsyncClient) -> None:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    tenant = await client.post(
        "/api/v1/tenants",
        headers=headers,
        json={"name": "tax-tenant", "slug": "tax-tenant"},
    )
    tenant_id = tenant.json()["id"]
    created = await client.post(
        "/api/v1/tax/rules",
        headers=headers,
        json={
            "tenant_id": tenant_id,
            "code": "CESS",
            "category": "GOODS",
            "jurisdiction": "IN-INTRA",
            "rate_bps": 100,
            "payer": "CUSTOMER",
            "kind": "CUSTOMER_TRANSACTION",
        },
    )
    assert created.status_code == 200, created.text
    assert created.json()["code"] == "CESS"

    calc = await client.post(
        "/api/v1/tax/calculate",
        headers={**headers, "X-Tenant-ID": tenant_id},
        json={
            "taxable_paise": 10000,
            "kind": "CUSTOMER_TRANSACTION",
            "category": "GOODS",
            "jurisdiction": "IN-INTRA",
            "tenant_id": tenant_id,
        },
    )
    assert calc.status_code == 200, calc.text
    codes = {line["code"] for line in calc.json()["lines"]}
    assert "CESS" in codes
    assert "CGST" in codes
    assert "SGST" in codes
