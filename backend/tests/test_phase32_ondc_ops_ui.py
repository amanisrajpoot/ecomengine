"""Phase 32: ONDC ops UI — admin session list and detail."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient


def _beckn_context(*, action: str, transaction_id: str) -> dict:
    return {
        "domain": "ONDC:RET10",
        "country": "IND",
        "city": "std:080",
        "action": action,
        "core_version": "1.2.0",
        "bap_id": "bap.example.com",
        "bap_uri": "https://bap.example.com/ondc",
        "bpp_id": "bpp.commerce-engine.local",
        "bpp_uri": "https://bpp.commerce-engine.local/ondc",
        "transaction_id": transaction_id,
        "message_id": str(uuid.uuid4()),
        "timestamp": datetime.now(UTC).isoformat(),
        "ttl": "PT30S",
    }


async def _admin_headers(client: AsyncClient) -> dict[str, str]:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _run_ondc_confirm(
    client: AsyncClient, headers: dict[str, str], ondc_headers: dict[str, str]
) -> tuple[str, str]:
    biz = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={"name": "ONDC Ops Kitchen", "type": "FOOD", "status": "ACTIVE"},
    )
    business_id = biz.json()["id"]
    loc = await client.post(
        f"/api/v1/businesses/{business_id}/locations",
        headers=headers,
        json={
            "name": "Store",
            "address": {
                "line1": "12 Main",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pincode": "560095",
            },
            "lat": 12.9352,
            "lng": 77.6245,
            "service_area": {"type": "radius", "radius_km": 8},
        },
    )
    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=headers,
        json={"name": "Meal"},
    )
    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product.json()['id']}/variants",
        headers=headers,
        json={"name": "Full", "base_price_paise": 32000},
    )
    _ = variant.json()["id"]

    txn = f"txn-{uuid.uuid4()}"
    search = await client.post(
        "/api/v1/integrations/ondc/search",
        headers=ondc_headers,
        json={
            "context": _beckn_context(action="search", transaction_id=txn),
            "message": {
                "intent": {
                    "fulfillment": {
                        "type": "Delivery",
                        "end": {"location": {"gps": "12.9355,77.6248"}},
                    }
                }
            },
        },
    )
    assert search.status_code == 200, search.text
    provider_id = search.json()["message"]["catalog"]["bpp/providers"][0]["id"]
    offer = search.json()["message"]["catalog"]["bpp/providers"][0]["items"][0]["id"]

    await client.post(
        "/api/v1/integrations/ondc/select",
        headers=ondc_headers,
        json={
            "context": _beckn_context(action="select", transaction_id=txn),
            "message": {
                "order": {
                    "provider": {"id": provider_id},
                    "items": [{"id": offer, "quantity": {"count": 1}}],
                }
            },
        },
    )
    await client.post(
        "/api/v1/integrations/ondc/init",
        headers=ondc_headers,
        json={
            "context": _beckn_context(action="init", transaction_id=txn),
            "message": {
                "order": {
                    "billing": {"phone": "9876501234"},
                    "provider": {"id": provider_id},
                    "items": [{"id": offer, "quantity": {"count": 1}}],
                }
            },
        },
    )
    confirm = await client.post(
        "/api/v1/integrations/ondc/confirm",
        headers=ondc_headers,
        json={
            "context": _beckn_context(action="confirm", transaction_id=txn),
            "message": {"order": {"provider": {"id": provider_id}}},
        },
    )
    assert confirm.status_code == 200, confirm.text
    status = await client.post(
        "/api/v1/integrations/ondc/status",
        headers=ondc_headers,
        json={
            "context": _beckn_context(action="status", transaction_id=txn),
            "message": {},
        },
    )
    assert status.status_code == 200, status.text
    order_id = status.json()["message"]["order"]["id"]
    return txn, order_id


@pytest.mark.asyncio
async def test_admin_lists_and_reads_ondc_sessions(client: AsyncClient) -> None:
    admin = await _admin_headers(client)
    tenant = await client.post(
        "/api/v1/tenants",
        headers=admin,
        json={"name": "p32-ondc", "slug": "p32-ondc"},
    )
    tenant_id = tenant.json()["id"]
    headers = {**admin, "X-Tenant-ID": tenant_id}
    ondc_headers = {"X-Tenant-ID": tenant_id}

    txn, order_id = await _run_ondc_confirm(client, headers, ondc_headers)

    listed = await client.get("/api/v1/integrations/ondc/sessions", headers=headers)
    assert listed.status_code == 200, listed.text
    rows = listed.json()
    assert len(rows) >= 1
    match = next((r for r in rows if r["transaction_id"] == txn), None)
    assert match is not None
    assert match["order_id"] == order_id
    assert match["stage"] == "CONFIRM"

    detail = await client.get(
        f"/api/v1/integrations/ondc/sessions/{match['id']}", headers=headers
    )
    assert detail.status_code == 200, detail.text
    assert detail.json()["transaction_id"] == txn
    assert detail.json()["bap_id"] == "bap.example.com"


@pytest.mark.asyncio
async def test_ondc_sessions_require_tenant_and_admin(client: AsyncClient) -> None:
    admin = await _admin_headers(client)
    missing_tenant = await client.get("/api/v1/integrations/ondc/sessions", headers=admin)
    assert missing_tenant.status_code == 400

    tenant = await client.post(
        "/api/v1/tenants",
        headers=admin,
        json={"name": "p32-ondc-auth", "slug": "p32-ondc-auth"},
    )
    tenant_id = tenant.json()["id"]
    headers = {**admin, "X-Tenant-ID": tenant_id}

    other = await client.post(
        "/api/v1/tenants",
        headers=admin,
        json={"name": "p32-other", "slug": "p32-other"},
    )
    other_id = other.json()["id"]
    ondc_headers = {"X-Tenant-ID": tenant_id}
    txn, _ = await _run_ondc_confirm(client, headers, ondc_headers)

    listed = await client.get("/api/v1/integrations/ondc/sessions", headers=headers)
    session_id = next(r["id"] for r in listed.json() if r["transaction_id"] == txn)

    wrong_tenant = await client.get(
        f"/api/v1/integrations/ondc/sessions/{session_id}",
        headers={**admin, "X-Tenant-ID": other_id},
    )
    assert wrong_tenant.status_code == 404
