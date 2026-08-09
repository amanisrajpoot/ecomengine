"""Phase 9: immutable financial ledger."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.ledger.postings import build_payment_captured_posting, build_refund_posting


def test_payment_captured_posting_is_balanced() -> None:
    import uuid

    order_id = uuid.uuid4()
    posting = build_payment_captured_posting(
        reference_key="payment-captured:test",
        order_id=order_id,
        pricing_snapshot={
            "subtotal_paise": 19900,
            "discount_paise": 0,
            "delivery_fee_paise": 3000,
            "platform_fee_paise": 500,
            "tax_paise": 1170,
            "total_paise": 24570,
        },
        payment_provider="cashfree",
        payment_id=str(uuid.uuid4()),
        commission_bps=1000,
        commission_gst_paise=358,  # ~18% of 1990
    )
    debits = sum(l.amount_paise for l in posting.lines if l.direction == "DEBIT")
    credits = sum(l.amount_paise for l in posting.lines if l.direction == "CREDIT")
    assert debits == credits == 24570
    accounts = {l.account for l in posting.lines}
    assert "PLATFORM_CASH" in accounts
    assert "MERCHANT_PAYABLE" in accounts
    assert "PLATFORM_COMMISSION" in accounts
    assert "RIDER_PAYABLE" in accounts


def test_cod_uses_customer_receivable() -> None:
    import uuid

    posting = build_payment_captured_posting(
        reference_key="payment-captured:cod",
        order_id=uuid.uuid4(),
        pricing_snapshot={
            "subtotal_paise": 10000,
            "discount_paise": 0,
            "delivery_fee_paise": 0,
            "platform_fee_paise": 0,
            "tax_paise": 500,
            "total_paise": 10500,
        },
        payment_provider="cod",
        payment_id=str(uuid.uuid4()),
        commission_bps=1000,
        commission_gst_paise=0,
    )
    debit_accounts = [l.account for l in posting.lines if l.direction == "DEBIT"]
    assert debit_accounts == ["CUSTOMER_RECEIVABLE"]


def test_refund_posting_is_balanced() -> None:
    import uuid

    posting = build_refund_posting(
        reference_key="payment-refund:x",
        order_id=uuid.uuid4(),
        refund_id=str(uuid.uuid4()),
        payment_id=str(uuid.uuid4()),
        amount_paise=1000,
        payment_provider="cashfree",
    )
    assert sum(l.amount_paise for l in posting.lines if l.direction == "DEBIT") == 1000
    assert sum(l.amount_paise for l in posting.lines if l.direction == "CREDIT") == 1000


async def _admin_headers(client: AsyncClient) -> dict[str, str]:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _priced_cart(client: AsyncClient, slug: str):
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
    cart_id = cart.json()["id"]
    await client.post(
        f"/api/v1/carts/{cart_id}/items",
        headers=headers,
        json={"variant_id": variant.json()["id"], "quantity": 1},
    )
    return headers, cart_id


@pytest.mark.asyncio
async def test_cod_checkout_posts_ledger(client: AsyncClient) -> None:
    headers, cart_id = await _priced_cart(client, "ledger-cod")
    checkout = await client.post(
        "/api/v1/orders/checkout",
        headers=headers,
        json={"cart_id": cart_id, "payment_provider": "cod"},
    )
    assert checkout.status_code == 200, checkout.text
    order = checkout.json()
    order_id = order["id"]
    total = order["pricing_snapshot"]["total_paise"]

    ledger = await client.get(f"/api/v1/orders/{order_id}/ledger", headers=headers)
    assert ledger.status_code == 200, ledger.text
    entries = ledger.json()
    assert entries
    assert all(e["event_type"] == "ORDER_PAYMENT_CAPTURED" for e in entries)
    debits = sum(e["amount_paise"] for e in entries if e["direction"] == "DEBIT")
    credits = sum(e["amount_paise"] for e in entries if e["direction"] == "CREDIT")
    assert debits == credits == total
    assert any(e["account"] == "CUSTOMER_RECEIVABLE" for e in entries)
    assert any(e["account"] == "MERCHANT_PAYABLE" for e in entries)

    balances = await client.get(
        "/api/v1/ledger/balances",
        headers=headers,
        params={"order_id": order_id},
    )
    assert balances.status_code == 200
    by_account = {b["account"]: b for b in balances.json()}
    assert by_account["CUSTOMER_RECEIVABLE"]["debit_paise"] == total


@pytest.mark.asyncio
async def test_cashfree_verify_posts_ledger_and_refund(client: AsyncClient) -> None:
    headers, cart_id = await _priced_cart(client, "ledger-cf")
    checkout = await client.post(
        "/api/v1/orders/checkout",
        headers=headers,
        json={"cart_id": cart_id, "payment_provider": "cashfree"},
    )
    assert checkout.status_code == 200, checkout.text
    order_id = checkout.json()["id"]

    # Not posted until capture.
    before = await client.get(f"/api/v1/orders/{order_id}/ledger", headers=headers)
    assert before.json() == []

    payments = await client.get(f"/api/v1/orders/{order_id}/payments", headers=headers)
    payment = payments.json()[0]
    verify = await client.post(
        f"/api/v1/orders/{order_id}/payments/verify",
        headers=headers,
        json={"provider": "cashfree", "provider_ref": payment["provider_ref"]},
    )
    assert verify.status_code == 200, verify.text

    ledger = await client.get(f"/api/v1/orders/{order_id}/ledger", headers=headers)
    entries = ledger.json()
    assert any(e["account"] == "PLATFORM_CASH" for e in entries)
    group_id = entries[0]["event_group_id"]
    event = await client.get(f"/api/v1/ledger/events/{group_id}", headers=headers)
    assert event.status_code == 200
    assert event.json()["debit_total_paise"] == event.json()["credit_total_paise"]

    # Idempotent re-verify should not duplicate ledger.
    await client.post(
        f"/api/v1/orders/{order_id}/payments/verify",
        headers=headers,
        json={"provider": "cashfree", "provider_ref": payment["provider_ref"]},
    )
    ledger2 = await client.get(f"/api/v1/orders/{order_id}/ledger", headers=headers)
    captured = [e for e in ledger2.json() if e["event_type"] == "ORDER_PAYMENT_CAPTURED"]
    assert len({e["event_group_id"] for e in captured}) == 1

    refund = await client.post(
        f"/api/v1/payments/{payment['id']}/refunds",
        headers=headers,
        json={"amount_paise": 500, "reason": "partial"},
    )
    assert refund.status_code == 200, refund.text
    ledger3 = await client.get(f"/api/v1/orders/{order_id}/ledger", headers=headers)
    assert any(e["event_type"] == "PAYMENT_REFUND" for e in ledger3.json())


@pytest.mark.asyncio
async def test_manual_adjustment(client: AsyncClient) -> None:
    headers = await _admin_headers(client)
    tenant = await client.post(
        "/api/v1/tenants",
        headers=headers,
        json={"name": "ledger-adj", "slug": "ledger-adj"},
    )
    headers["X-Tenant-ID"] = tenant.json()["id"]
    adj = await client.post(
        "/api/v1/ledger/adjustments",
        headers=headers,
        json={
            "reference_key": "manual-adj-1",
            "reason": "goodwill",
            "lines": [
                {
                    "account": "PLATFORM_CLEARING",
                    "direction": "DEBIT",
                    "amount_paise": 100,
                },
                {
                    "account": "MERCHANT_PAYABLE",
                    "direction": "CREDIT",
                    "amount_paise": 100,
                },
            ],
        },
    )
    assert adj.status_code == 200, adj.text
    assert adj.json()["event_type"] == "MANUAL_ADJUSTMENT"
    assert adj.json()["debit_total_paise"] == 100

    # Unbalanced rejected.
    bad = await client.post(
        "/api/v1/ledger/adjustments",
        headers=headers,
        json={
            "reference_key": "manual-adj-bad",
            "lines": [
                {"account": "PLATFORM_CLEARING", "direction": "DEBIT", "amount_paise": 100},
                {"account": "MERCHANT_PAYABLE", "direction": "CREDIT", "amount_paise": 50},
            ],
        },
    )
    assert bad.status_code == 422
