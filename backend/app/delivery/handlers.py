"""Event bus handlers for automatic rider dispatch."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.delivery.dispatch import auto_dispatch_order

_registered = False


def register_dispatch_handlers() -> None:
    global _registered
    if _registered:
        return
    _registered = True
    from app.core.events import event_bus

    event_bus.subscribe("OrderReady", _on_dispatch_event)
    event_bus.subscribe("PaymentCaptured", _on_dispatch_event)


async def _on_dispatch_event(event_name: str, payload: dict[str, Any]) -> None:
    order_id = payload.get("order_id")
    tenant_id = payload.get("tenant_id")
    profile = payload.get("profile")
    if not order_id or not tenant_id:
        return

    if event_name == "OrderReady" and profile == "COURIER":
        return
    if event_name == "PaymentCaptured" and profile != "COURIER":
        return

    settings = get_settings()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    try:
        async with session_factory() as db:
            await auto_dispatch_order(
                db,
                tenant_id=uuid.UUID(tenant_id),
                order_id=uuid.UUID(order_id),
            )
    finally:
        await engine.dispose()
