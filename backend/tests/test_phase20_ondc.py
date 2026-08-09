"""Phase 20: ONDC adapter golden path (search → confirm)."""

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


@pytest.mark.asyncio
async def test_ondc_food_search_to_confirm(client: AsyncClient) -> None:
    admin = await _admin_headers(client)
    tenant = await client.post(
        "/api/v1/tenants",
        headers=admin,
        json={"name": "ondc-tenant", "slug": "ondc-tenant"},
    )
    tenant_id = tenant.json()["id"]
    headers = {**admin, "X-Tenant-ID": tenant_id}

    biz = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={"name": "ONDC Kitchen", "type": "FOOD", "status": "ACTIVE"},
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
    location_id = loc.json()["id"]
    product = await client.post(
        f"/api/v1/businesses/{business_id}/products",
        headers=headers,
        json={"name": "Biryani"},
    )
    variant = await client.post(
        f"/api/v1/businesses/{business_id}/products/{product.json()['id']}/variants",
        headers=headers,
        json={"name": "Full", "base_price_paise": 32000},
    )
    variant_id = variant.json()["id"]

    meta = await client.get("/api/v1/integrations/ondc/meta")
    assert meta.status_code == 200
    assert meta.json()["mock_mode"] is True

    txn = f"txn-{uuid.uuid4()}"
    ondc_headers = {"X-Tenant-ID": tenant_id}

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
    assert search.json()["context"]["action"] == "on_search"
    providers = search.json()["message"]["catalog"]["bpp/providers"]
    assert providers
    provider_id = providers[0]["id"]
    offer = providers[0]["items"][0]["id"]

    select = await client.post(
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
    assert select.status_code == 200, select.text
    assert select.json()["context"]["action"] == "on_select"

    init = await client.post(
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
    assert init.status_code == 200, init.text
    assert init.json()["context"]["action"] == "on_init"
    quote = init.json()["message"]["order"]["quote"]["price"]["value"]
    assert float(quote) > 0

    confirm = await client.post(
        "/api/v1/integrations/ondc/confirm",
        headers=ondc_headers,
        json={
            "context": _beckn_context(action="confirm", transaction_id=txn),
            "message": {"order": {"provider": {"id": provider_id}}},
        },
    )
    assert confirm.status_code == 200, confirm.text
    assert confirm.json()["context"]["action"] == "on_confirm"

    status = await client.post(
        "/api/v1/integrations/ondc/status",
        headers=ondc_headers,
        json={
            "context": _beckn_context(action="status", transaction_id=txn),
            "message": {},
        },
    )
    assert status.status_code == 200, status.text
    body = status.json()
    assert body["context"]["action"] == "on_status"
    assert body["message"]["order"]["state"] == "Created"
    real_order_id = body["message"]["order"]["id"]

    order = await client.get(f"/api/v1/orders/{real_order_id}", headers=headers)
    assert order.status_code == 200
    assert order.json()["status"] == "PAYMENT_CONFIRMED"
    assert order.json()["metadata"].get("channel") == "ondc"

    cancel = await client.post(
        "/api/v1/integrations/ondc/cancel",
        headers=ondc_headers,
        json={
            "context": _beckn_context(action="cancel", transaction_id=txn),
            "message": {"order_id": real_order_id},
        },
    )
    assert cancel.status_code == 200, cancel.text
    assert cancel.json()["message"]["order"]["state"] == "Cancelled"

    final = await client.get(f"/api/v1/orders/{real_order_id}", headers=headers)
    assert final.json()["status"] == "CANCELLED"
