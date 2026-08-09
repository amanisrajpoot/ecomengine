"""Order domain services: checkout from cart + state transitions."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.businesses.models import Business
from app.cart.models import Cart, CartItem
from app.cart.service import get_cart
from app.core.errors import AppError
from app.core.events import event_bus
from app.orders.models import Order, OrderItem, OrderStatusEvent
from app.orders.schemas import CheckoutRequest, OrderTransitionRequest
from app.orders.states import registry


async def _load_order_graph(
    db: AsyncSession, *, tenant_id: uuid.UUID, order_id: uuid.UUID
) -> tuple[Order, list[OrderItem], list[OrderStatusEvent]]:
    order = await db.scalar(
        select(Order).where(Order.id == order_id, Order.tenant_id == tenant_id)
    )
    if not order:
        raise AppError("ORDER_NOT_FOUND", "Order not found", 404)
    items = list(
        await db.scalars(select(OrderItem).where(OrderItem.order_id == order.id))
    )
    events = list(
        await db.scalars(
            select(OrderStatusEvent)
            .where(OrderStatusEvent.order_id == order.id)
            .order_by(OrderStatusEvent.created_at.asc())
        )
    )
    return order, items, events


async def checkout_from_cart(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: CheckoutRequest,
) -> tuple[Order, list[OrderItem], list[OrderStatusEvent]]:
    cart, cart_items = await get_cart(db, tenant_id=tenant_id, cart_id=payload.cart_id)
    if cart.status != "OPEN":
        raise AppError("CART_NOT_OPEN", "Cart is not open for checkout", 409)
    if not cart_items:
        raise AppError("CART_EMPTY", "Cannot checkout an empty cart", 400)
    if not cart.pricing_snapshot or "total_paise" not in cart.pricing_snapshot:
        raise AppError("CART_NOT_PRICED", "Cart has no pricing snapshot", 400)

    business: Business | None = None
    if cart.business_id:
        business = await db.get(Business, cart.business_id)
    profile = payload.state_machine_profile or registry.profile_for_business_type(
        business.type if business else None
    )
    machine = registry.get(profile)

    order = Order(
        tenant_id=tenant_id,
        customer_id=cart.customer_id,
        business_id=cart.business_id,
        location_id=cart.location_id,
        cart_id=cart.id,
        status=machine.initial_status,
        state_machine_profile=profile,
        currency=cart.currency,
        pricing_snapshot=cart.pricing_snapshot,
        fulfillment_type=payload.fulfillment_type,
        payment_method="COD" if (
            payload.payment_provider == "cod" or payload.payment_method == "COD"
        ) else "ONLINE",
        placed_at=datetime.now(UTC),
        metadata_json={"created_by": str(user_id)},
    )
    db.add(order)
    await db.flush()

    for item in cart_items:
        db.add(
            OrderItem(
                order_id=order.id,
                variant_id=item.variant_id,
                bundle_id=item.bundle_id,
                name_snapshot=item.name_snapshot,
                quantity=item.quantity,
                unit_price_paise=item.unit_price_paise,
                modifiers_paise=item.modifiers_paise,
                addons_snapshot=item.addons if isinstance(item.addons, list) else [],
                metadata_json=item.metadata_json or {},
            )
        )

    db.add(
        OrderStatusEvent(
            order_id=order.id,
            from_status=None,
            to_status=order.status,
            actor_user_id=user_id,
            actor_role="customer",
            reason="checkout",
        )
    )
    cart.status = "CHECKED_OUT"
    await db.commit()
    await db.refresh(order)

    await event_bus.publish(
        "OrderCreated",
        {
            "tenant_id": str(tenant_id),
            "order_id": str(order.id),
            "status": order.status,
            "profile": profile,
        },
    )

    # Legacy payment_method maps COD→cod; otherwise use payment_provider (default cashfree).
    provider = "cod" if payload.payment_method == "COD" else payload.payment_provider

    from app.payments.schemas import InitiatePaymentBody
    from app.payments.service import initiate_payment

    await initiate_payment(
        db,
        tenant_id=tenant_id,
        order_id=order.id,
        payload=InitiatePaymentBody(
            provider=provider,
            return_url=payload.return_url,
            notify_url=payload.notify_url,
            customer_phone=payload.customer_phone,
            customer_email=payload.customer_email,
            idempotency_key=f"checkout-{order.id}",
        ),
        actor_user_id=user_id,
    )
    return await _load_order_graph(db, tenant_id=tenant_id, order_id=order.id)


async def transition_order(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    order_id: uuid.UUID,
    payload: OrderTransitionRequest,
    actor_user_id: uuid.UUID | None,
) -> tuple[Order, list[OrderItem], list[OrderStatusEvent]]:
    order, items, _events = await _load_order_graph(
        db, tenant_id=tenant_id, order_id=order_id
    )
    machine = registry.get(order.state_machine_profile)
    machine.assert_can_transition(order.status, payload.to_status, payload.actor)

    previous = order.status
    order.status = payload.to_status
    db.add(
        OrderStatusEvent(
            order_id=order.id,
            from_status=previous,
            to_status=payload.to_status,
            actor_user_id=actor_user_id,
            actor_role=payload.actor,
            reason=payload.reason,
        )
    )
    await db.commit()
    await db.refresh(order)

    event_name = {
        "PAYMENT_CONFIRMED": "PaymentCaptured",
        "ACCEPTED": "OrderAccepted",
        "READY": "OrderReady",
        "PICKED_UP": "OrderPickedUp",
        "DELIVERED": "OrderDelivered",
        "CANCELLED": "OrderCancelled",
    }.get(payload.to_status, "OrderStatusChanged")
    await event_bus.publish(
        event_name,
        {
            "tenant_id": str(tenant_id),
            "order_id": str(order.id),
            "from_status": previous,
            "to_status": payload.to_status,
            "profile": order.state_machine_profile,
        },
    )
    return await _load_order_graph(db, tenant_id=tenant_id, order_id=order.id)


async def get_order(
    db: AsyncSession, *, tenant_id: uuid.UUID, order_id: uuid.UUID
) -> tuple[Order, list[OrderItem], list[OrderStatusEvent]]:
    return await _load_order_graph(db, tenant_id=tenant_id, order_id=order_id)


async def list_orders(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID | None = None,
    customer_id: uuid.UUID | None = None,
    status: str | None = None,
) -> list[Order]:
    stmt = select(Order).where(Order.tenant_id == tenant_id)
    if business_id:
        stmt = stmt.where(Order.business_id == business_id)
    if customer_id:
        stmt = stmt.where(Order.customer_id == customer_id)
    if status:
        stmt = stmt.where(Order.status == status)
    stmt = stmt.order_by(Order.created_at.desc())
    return list(await db.scalars(stmt))
