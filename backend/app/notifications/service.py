"""Notification dispatch and query services."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.identity.models import CustomerProfile, User
from app.notifications.channel import SendNotificationRequest
from app.notifications.models import Notification
from app.notifications.registry import channel_registry
from app.orders.models import Order
from app.payments.models import Payment


def _format_amount_paise(paise: int) -> str:
    return f"₹{paise / 100:.2f}"


def render_message(*, event_name: str, order: Order) -> str:
    short_id = str(order.id)[:8]
    total = int(order.pricing_snapshot.get("total_paise") or 0)
    amount = _format_amount_paise(total) if total else ""
    templates = {
        "OrderCreated": f"Order {short_id} placed. Total {amount}.".strip(),
        "PaymentCaptured": f"Payment received for order {short_id}. Total {amount}.".strip(),
        "OrderAccepted": f"Order {short_id} accepted by the store.",
        "OrderReady": f"Order {short_id} is ready.",
        "OrderDelivered": f"Order {short_id} delivered. Thank you!",
        "OrderCancelled": f"Order {short_id} was cancelled.",
        "RiderAssigned": f"A rider is on the way for order {short_id}.",
    }
    return templates.get(event_name, f"Update for order {short_id}: {event_name}.")


async def _resolve_recipient_phone(
    db: AsyncSession, *, order: Order
) -> str | None:
    meta = order.metadata_json if isinstance(order.metadata_json, dict) else {}
    for key in ("customer_phone", "ondc_customer_phone"):
        phone = meta.get(key)
        if phone:
            return str(phone)
    payment = await db.scalar(
        select(Payment)
        .where(Payment.order_id == order.id)
        .order_by(Payment.created_at.desc())
        .limit(1)
    )
    if payment and isinstance(payment.checkout_payload, dict):
        phone = payment.checkout_payload.get("customer_phone")
        if phone:
            return str(phone)
    profile = await db.get(CustomerProfile, order.customer_id)
    if profile:
        customer_user = await db.get(User, profile.user_id)
        if customer_user and customer_user.phone:
            return customer_user.phone
    return None


async def dispatch_order_notification(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    order_id: uuid.UUID,
    event_name: str,
) -> Notification | None:
    order = await db.scalar(
        select(Order).where(Order.id == order_id, Order.tenant_id == tenant_id)
    )
    if not order:
        return None
    phone = await _resolve_recipient_phone(db, order=order)
    if not phone:
        return None

    profile = await db.get(CustomerProfile, order.customer_id)
    notify_user_id = profile.user_id if profile else None

    settings = get_settings()
    channel_name = settings.notifications_default_channel
    body = render_message(event_name=event_name, order=order)
    notification = Notification(
        tenant_id=tenant_id,
        user_id=notify_user_id,
        order_id=order.id,
        event_name=event_name,
        channel="sms",
        recipient=phone,
        subject=None,
        body=body,
        status="PENDING",
        metadata_json={"order_status": order.status},
    )
    db.add(notification)
    await db.flush()

    channel = channel_registry.get(channel_name)
    result = await channel.send(
        SendNotificationRequest(recipient=phone, subject=None, body=body)
    )
    notification.provider = result.provider
    notification.provider_ref = result.provider_ref
    notification.status = result.status
    notification.metadata_json = {
        **notification.metadata_json,
        "provider_raw": result.raw,
    }
    await db.commit()
    await db.refresh(notification)
    return notification


async def list_notifications(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    order_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    limit: int = 50,
) -> list[Notification]:
    stmt = select(Notification).where(Notification.tenant_id == tenant_id)
    if order_id:
        stmt = stmt.where(Notification.order_id == order_id)
    if user_id:
        stmt = stmt.where(Notification.user_id == user_id)
    stmt = stmt.order_by(Notification.created_at.desc()).limit(max(1, min(limit, 200)))
    return list(await db.scalars(stmt))
