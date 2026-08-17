"""Phase 9: ledger entries on payment capture and refund."""

from __future__ import annotations

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


async def _checkout_order(client: AsyncClient, headers: dict[str, str], slug: str) -> str:
    admin = await _admin_headers(client, headers["X-Tenant-ID"])
    biz = await client.post(
        "/api/v1/businesses",
        headers=admin,
        json={"name": f"Ledger {slug}", "type": "FOOD", "status": "ACTIVE"},
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
    return order.json()["id"]


def _sum_direction(entries: list[dict], direction: str) -> int:
    return sum(e["amount_paise"] for e in entries if e["direction"] == direction)


@pytest.mark.asyncio
async def test_payment_capture_posts_balanced_ledger(client: AsyncClient) -> None:
    headers = await _tenant_and_customer(client, "p9-capture")
    admin = await _admin_headers(client, headers["X-Tenant-ID"])
    order_id = await _checkout_order(client, headers, "cap")

    pay = await client.post(
        f"/api/v1/orders/{order_id}/payments",
        headers={**headers, "Idempotency-Key": "p9-cap-key"},
        json={"provider": "COD"},
    )
    assert pay.status_code == 200, pay.text
    payment_id = pay.json()["id"]

    ledger = await client.get(f"/api/v1/orders/{order_id}/ledger-entries", headers=admin)
    assert ledger.status_code == 200, ledger.text
    groups = ledger.json()
    assert len(groups) == 1
    group = groups[0]
    assert group["event_type"] == "PAYMENT_CAPTURED"
    assert group["event_group_id"] == payment_id
    entries = group["entries"]
    assert len(entries) == 5

    debits = _sum_direction(entries, "DEBIT")
    credits = _sum_direction(entries, "CREDIT")
    assert debits == credits
    assert debits == pay.json()["amount_paise"]

    accounts = {e["account"]: e for e in entries}
    assert accounts["PLATFORM_CASH"]["direction"] == "DEBIT"
    assert accounts["MERCHANT_PAYABLE"]["direction"] == "CREDIT"
    assert accounts["TAX_LIABILITY"]["direction"] == "CREDIT"
    assert accounts["PLATFORM_REVENUE"]["direction"] == "CREDIT"
    assert accounts["DELIVERY_PAYABLE"]["direction"] == "CREDIT"

    by_group = await client.get(
        f"/api/v1/ledger/event-groups/{payment_id}",
        headers=admin,
    )
    assert by_group.status_code == 200, by_group.text
    assert len(by_group.json()["entries"]) == 5


@pytest.mark.asyncio
async def test_ledger_idempotent_on_duplicate_capture(client: AsyncClient) -> None:
    headers = await _tenant_and_customer(client, "p9-idem")
    admin = await _admin_headers(client, headers["X-Tenant-ID"])
    order_id = await _checkout_order(client, headers, "idem")

    init = await client.post(
        f"/api/v1/orders/{order_id}/payments",
        headers={**headers, "Idempotency-Key": "p9-rzp"},
        json={"provider": "RAZORPAY"},
    )
    payment_id = init.json()["id"]

    first = await client.post(f"/api/v1/payments/{payment_id}/capture", headers=admin)
    second = await client.post(f"/api/v1/payments/{payment_id}/capture", headers=admin)
    assert first.status_code == 200
    assert second.status_code == 200

    ledger = await client.get(f"/api/v1/orders/{order_id}/ledger-entries", headers=admin)
    assert len(ledger.json()) == 1
    assert len(ledger.json()[0]["entries"]) == 5


@pytest.mark.asyncio
async def test_refund_posts_reversal_ledger(client: AsyncClient) -> None:
    headers = await _tenant_and_customer(client, "p9-refund")
    admin = await _admin_headers(client, headers["X-Tenant-ID"])
    order_id = await _checkout_order(client, headers, "ref")

    pay = await client.post(
        f"/api/v1/orders/{order_id}/payments",
        headers={**headers, "Idempotency-Key": "p9-ref"},
        json={"provider": "COD"},
    )
    payment_id = pay.json()["id"]
    amount = pay.json()["amount_paise"]

    refund = await client.post(
        f"/api/v1/payments/{payment_id}/refunds",
        headers=admin,
        json={"reason": "test refund"},
    )
    assert refund.status_code == 200, refund.text
    refund_id = refund.json()["id"]

    ledger = await client.get(f"/api/v1/orders/{order_id}/ledger-entries", headers=admin)
    groups = ledger.json()
    assert len(groups) == 2

    capture = next(g for g in groups if g["event_type"] == "PAYMENT_CAPTURED")
    reversal = next(g for g in groups if g["event_type"] == "REFUND_COMPLETED")
    assert reversal["event_group_id"] == refund_id

    assert _sum_direction(capture["entries"], "DEBIT") == amount
    assert _sum_direction(reversal["entries"], "CREDIT") == amount
    assert _sum_direction(reversal["entries"], "DEBIT") == amount

    cash_reversal = next(
        e for e in reversal["entries"] if e["account"] == "PLATFORM_CASH"
    )
    assert cash_reversal["direction"] == "CREDIT"
    assert cash_reversal["amount_paise"] == amount
