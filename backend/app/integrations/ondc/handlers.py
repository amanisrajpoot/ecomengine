"""Subscribe ONDC adapter to domain events."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.events import event_bus
from app.integrations.ondc.callbacks import record_status_callback
from app.orders.models import Order


def register_ondc_handlers() -> None:
    event_bus.subscribe("OrderStatusChanged", _on_order_status)
    event_bus.subscribe("OrderAccepted", _on_order_status)
    event_bus.subscribe("OrderDelivered", _on_order_status)
    event_bus.subscribe("OrderCancelled", _on_order_status)


async def _on_order_status(_event: str, payload: dict[str, Any]) -> None:
    order_id = payload.get("order_id")
    tenant_id = payload.get("tenant_id")
    if not order_id or not tenant_id:
        return

    settings = get_settings()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    try:
        async with session_factory() as db:
            import uuid

            order = await db.get(Order, uuid.UUID(order_id))
            if not order:
                return
            await record_status_callback(
                db,
                tenant_id=uuid.UUID(tenant_id),
                order=order,
                from_status=payload.get("from_status"),
                to_status=payload.get("to_status") or order.status,
            )
    finally:
        await engine.dispose()
