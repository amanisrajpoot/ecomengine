"""Event bus handlers for order lifecycle notifications."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.notifications.service import dispatch_order_notification

_ORDER_EVENTS = frozenset(
    {
        "OrderCreated",
        "PaymentCaptured",
        "OrderAccepted",
        "OrderReady",
        "OrderDelivered",
        "OrderCancelled",
        "RiderAssigned",
    }
)

_registered = False


def register_notification_handlers() -> None:
    global _registered
    if _registered:
        return
    _registered = True
    from app.core.events import event_bus

    for event_name in _ORDER_EVENTS:
        event_bus.subscribe(event_name, _on_order_event)


async def _on_order_event(event_name: str, payload: dict[str, Any]) -> None:
    order_id = payload.get("order_id")
    tenant_id = payload.get("tenant_id")
    if not order_id or not tenant_id:
        return

    settings = get_settings()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    try:
        async with session_factory() as db:
            await dispatch_order_notification(
                db,
                tenant_id=uuid.UUID(tenant_id),
                order_id=uuid.UUID(order_id),
                event_name=event_name,
            )
    finally:
        await engine.dispose()
