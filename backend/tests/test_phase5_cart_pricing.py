"""Phase 5: cart + pricing pipeline with tax stub."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.pricing.engine import price_items
from app.pricing.schemas import PricingContext, PricingInputItem
from app.taxation.service import calculate_customer_transaction_tax


async def _admin_headers(client: AsyncClient) -> dict[str, str]:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _food_catalog(client: AsyncClient, slug: str):
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
    product_id = product.json()["id"]
    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product_id}/variants",
        headers=headers,
        json={"name": "Regular", "base_price_paise": 19900},
    )
    addon = await client.post(
        f"/api/v1/businesses/{business_id}/addons",
        headers=headers,
        json={"name": "Cheese", "price_paise": 3000, "max_qty": 2},
    )
    return headers, business_id, variant.json()["id"], addon.json()["id"]


def test_pricing_pipeline_breakdown_invariant() -> None:
    breakdown = price_items(
        [
            PricingInputItem(
                name="Burger — Regular",
                quantity=2,
                unit_price_paise=19900,
                modifiers_paise=3000,
            )
        ],
        PricingContext(
            discount_paise=5000,
            delivery_fee_paise=3000,
            platform_fee_paise=500,
            tax_rate_bps=500,
            tax_jurisdiction="IN-INTRA",
        ),
    )
    # subtotal = (19900+3000)*2 = 45800
    assert breakdown.subtotal_paise == 45800
    assert breakdown.discount_paise == 5000
    taxable = 45800 - 5000 + 3000 + 500
    assert breakdown.tax_paise == (taxable * 500) // 10_000
    assert len(breakdown.tax_lines) == 2
    assert {t.code for t in breakdown.tax_lines} == {"CGST", "SGST"}
    assert sum(t.amount_paise for t in breakdown.tax_lines) == breakdown.tax_paise
    breakdown.assert_invariant()


def test_tax_stub_igst_split() -> None:
    result = calculate_customer_transaction_tax(
        taxable_paise=10_000, rate_bps=500, jurisdiction="IN-INTER"
    )
    assert result.tax_paise == 500
    assert len(result.lines) == 1
    assert result.lines[0].code == "IGST"


@pytest.mark.asyncio
async def test_cart_with_addons_pricing_snapshot(client: AsyncClient) -> None:
    headers, business_id, variant_id, addon_id = await _food_catalog(client, "cart-food")

    cart = await client.post(
        "/api/v1/carts",
        headers=headers,
        json={
            "business_id": business_id,
            "delivery_fee_paise": 3000,
            "platform_fee_paise": 500,
            "discount_paise": 0,
        },
    )
    assert cart.status_code == 200, cart.text
    cart_id = cart.json()["id"]
    assert cart.json()["pricing_snapshot"]["total_paise"] >= 0

    updated = await client.post(
        f"/api/v1/carts/{cart_id}/items",
        headers=headers,
        json={
            "variant_id": variant_id,
            "quantity": 1,
            "addons": [{"addon_id": addon_id, "quantity": 1}],
        },
    )
    assert updated.status_code == 200, updated.text
    snap = updated.json()["pricing_snapshot"]
    assert snap["subtotal_paise"] == 19900 + 3000
    assert snap["delivery_fee_paise"] == 3000
    assert snap["platform_fee_paise"] == 500
    assert snap["tax_paise"] > 0
    assert len(snap["tax_lines"]) == 2
    expected_total = (
        snap["subtotal_paise"]
        - snap["discount_paise"]
        + snap["delivery_fee_paise"]
        + snap["platform_fee_paise"]
        + snap["other_fees_paise"]
        + snap["tax_paise"]
    )
    assert snap["total_paise"] == expected_total
    assert len(updated.json()["items"]) == 1

    fees = await client.patch(
        f"/api/v1/carts/{cart_id}/fees",
        headers=headers,
        json={"discount_paise": 2000},
    )
    assert fees.status_code == 200
    assert fees.json()["pricing_snapshot"]["discount_paise"] == 2000
    assert fees.json()["pricing_snapshot"]["total_paise"] < snap["total_paise"]


@pytest.mark.asyncio
async def test_pricing_quote_endpoint(client: AsyncClient) -> None:
    headers = await _admin_headers(client)
    resp = await client.post(
        "/api/v1/pricing/quote",
        headers=headers,
        json={
            "items": [
                {
                    "name": "Item",
                    "quantity": 1,
                    "unit_price_paise": 10000,
                    "modifiers_paise": 0,
                }
            ],
            "context": {
                "delivery_fee_paise": 0,
                "platform_fee_paise": 0,
                "tax_rate_bps": 500,
            },
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["subtotal_paise"] == 10000
    assert body["tax_paise"] == 500
    assert body["total_paise"] == 10500
