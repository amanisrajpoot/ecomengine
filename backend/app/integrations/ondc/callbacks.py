"""Outbound ONDC callbacks to buyer apps (BAP)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.integrations.ondc.mapper import map_order_state
from app.integrations.ondc.models import OndcSession
from app.integrations.ondc.schemas import BecknContext, BecknResponse
from app.orders.models import Order


def _on_action(action: str) -> str:
    return f"on_{action}" if not action.startswith("on_") else action


async def record_status_callback(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    order: Order,
    from_status: str | None,
    to_status: str,
) -> None:
    session = await db.scalar(
        select(OndcSession).where(
            OndcSession.tenant_id == tenant_id,
            OndcSession.order_id == order.id,
        )
    )
    if not session:
        return

    ctx_data = session.context_json or {}
    context = BecknContext.model_validate(ctx_data)
    response = BecknResponse(
        context=context.model_copy(
            update={
                "action": _on_action("status"),
                "message_id": str(uuid.uuid4()),
                "timestamp": datetime.now(UTC).isoformat(),
            }
        ),
        message={
            "order": {
                "id": str(order.id),
                "state": map_order_state(to_status),
                "provider": {"id": session.selected_items[0].get("provider_id") if session.selected_items else None},
            },
            "meta": {"from_status": from_status, "to_status": to_status},
        },
    )
    payload = response.model_dump(mode="json")
    log = list(session.callback_log or [])
    log.append({"action": "on_status", "payload": payload, "at": datetime.now(UTC).isoformat()})
    session.callback_log = log
    await db.commit()

    settings = get_settings()
    if settings.ondc_mock or not settings.ondc_send_callbacks:
        return

    # Production path: POST to BAP callback URL (signing TBD).
    import httpx

    callback_url = session.bap_uri.rstrip("/") + "/on_status"
    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(callback_url, json=payload)
