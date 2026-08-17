"""Order checkout and state transitions."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.businesses.service import get_business
from app.cart.service import get_cart, recalculate_cart_pricing
from app.catalog.models import Bundle, Variant
from app.catalog.service import get_product
from app.core.errors import AppError
from app.fulfillment import service as fulfillment_service
from app.orders.models import Order, OrderItem, OrderStatusEvent
from app.orders.schemas import OrderCheckout, OrderTransition
from app.orders.states import profile_for_business_type, registry


async def _get_order(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    order_id: uuid.UUID,
    customer_id: uuid.UUID | None = None,
) -> Order:
    order = await db.scalar(
        select(Order)
        .options(selectinload(Order.items), selectinload(Order.status_events))
        .where(Order.id == order_id, Order.tenant_id == tenant_id)
    )
    if not order:
        raise AppError("ORDER_NOT_FOUND", "Order not found", status_code=404)
    if customer_id is not None and order.customer_id != customer_id:
        raise AppError("FORBIDDEN", "Order does not belong to this customer", status_code=403)
    return order


async def _record_status_event(
    db: AsyncSession,
    *,
    order: Order,
    from_status: str | None,
    to_status: str,
    actor_user_id: uuid.UUID | None = None,
    reason: str | None = None,
) -> OrderStatusEvent:
    event = OrderStatusEvent(
        order_id=order.id,
        from_status=from_status,
        to_status=to_status,
        actor_user_id=actor_user_id,
        reason=reason,
        created_at=datetime.now(timezone.utc),
    )
    db.add(event)
    return event


async def _item_name_snapshot(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    business_id: uuid.UUID,
    cart_item,
) -> tuple[str, int, list]:
    if cart_item.variant_id is not None:
        variant = await db.get(Variant, cart_item.variant_id)
        if not variant or variant.tenant_id != tenant_id:
            raise AppError("VARIANT_NOT_FOUND", "Variant not found", status_code=404)
        product = await get_product(
            db,
            tenant_id=tenant_id,
            business_id=business_id,
            product_id=variant.product_id,
        )
        name = f"{product.name} ({variant.name})"
        unit_price = cart_item.unit_price_paise or variant.base_price_paise
        return name, unit_price, cart_item.addons or []
    if cart_item.bundle_id is not None:
        bundle = await db.get(Bundle, cart_item.bundle_id)
        if not bundle or bundle.tenant_id != tenant_id:
            raise AppError("BUNDLE_NOT_FOUND", "Bundle not found", status_code=404)
        unit_price = cart_item.unit_price_paise or (bundle.price_paise or 0)
        return bundle.name, unit_price, []
    raise AppError("INVALID_CART_ITEM", "Cart item has no variant or bundle", status_code=400)


async def _apply_transition(
    db: AsyncSession,
    *,
    order: Order,
    payload: OrderTransition,
    actor_user_id: uuid.UUID | None = None,
) -> None:
    machine = registry.get(order.state_machine_profile)
    from_status = order.status
    to_status = payload.to_status
    if not machine.can_transition(from_status, to_status):
        raise AppError(
            "INVALID_TRANSITION",
            f"Cannot transition from {from_status} to {to_status}",
            status_code=400,
        )
    order.status = to_status
    await _record_status_event(
        db,
        order=order,
        from_status=from_status,
        to_status=to_status,
        actor_user_id=actor_user_id,
        reason=payload.reason,
    )


async def checkout_from_cart(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    payload: OrderCheckout,
) -> Order:
    cart = await get_cart(
        db,
        tenant_id=tenant_id,
        cart_id=payload.cart_id,
        customer_id=customer_id,
    )
    if not cart.business_id:
        raise AppError("CART_INCOMPLETE", "Cart must have a business", status_code=400)
    if not cart.items:
        raise AppError("CART_EMPTY", "Cannot checkout an empty cart", status_code=400)

    cart, pricing_dict = await recalculate_cart_pricing(
        db,
        tenant_id=tenant_id,
        cart_id=cart.id,
        customer_id=customer_id,
    )

    business = await get_business(
        db, tenant_id=tenant_id, business_id=cart.business_id
    )
    profile = profile_for_business_type(business.type)
    machine = registry.get(profile)
    now = datetime.now(timezone.utc)

    order = Order(
        tenant_id=tenant_id,
        customer_id=customer_id,
        business_id=cart.business_id,
        location_id=cart.location_id,
        status=machine.initial_status(),
        state_machine_profile=profile,
        currency=cart.currency,
        pricing_snapshot=pricing_dict,
        fulfillment_type=payload.fulfillment_type,
        placed_at=now,
    )
    db.add(order)
    await db.flush()

    for cart_item in cart.items:
        name, unit_price, addons = await _item_name_snapshot(
            db,
            tenant_id=tenant_id,
            business_id=cart.business_id,
            cart_item=cart_item,
        )
        db.add(
            OrderItem(
                order_id=order.id,
                variant_id=cart_item.variant_id,
                name_snapshot=name,
                quantity=cart_item.quantity,
                unit_price_paise=unit_price,
                addons_snapshot=addons,
                meta=cart_item.meta,
            )
        )

    await _record_status_event(
        db,
        order=order,
        from_status=None,
        to_status=order.status,
        actor_user_id=customer_id,
        reason="checkout",
    )

    await _apply_transition(
        db,
        order=order,
        payload=OrderTransition(to_status="PAYMENT_PENDING", reason="checkout"),
        actor_user_id=customer_id,
    )

    await fulfillment_service.create_for_order(
        db,
        tenant_id=tenant_id,
        order_id=order.id,
        fulfillment_type=payload.fulfillment_type,
    )

    await db.commit()
    return await _get_order(db, tenant_id=tenant_id, order_id=order.id)


async def get_order(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    order_id: uuid.UUID,
    customer_id: uuid.UUID | None = None,
) -> Order:
    return await _get_order(
        db, tenant_id=tenant_id, order_id=order_id, customer_id=customer_id
    )


async def list_orders(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID | None = None,
    business_id: uuid.UUID | None = None,
    status: str | None = None,
) -> list[Order]:
    stmt = (
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.tenant_id == tenant_id)
    )
    if customer_id is not None:
        stmt = stmt.where(Order.customer_id == customer_id)
    if business_id is not None:
        stmt = stmt.where(Order.business_id == business_id)
    if status is not None:
        stmt = stmt.where(Order.status == status)
    stmt = stmt.order_by(Order.created_at.desc())
    return list(await db.scalars(stmt))


async def transition_order(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    order_id: uuid.UUID,
    payload: OrderTransition,
    actor_user_id: uuid.UUID | None = None,
) -> Order:
    order = await _get_order(db, tenant_id=tenant_id, order_id=order_id)
    await _apply_transition(
        db,
        order=order,
        payload=payload,
        actor_user_id=actor_user_id,
    )
    await db.commit()
    return await _get_order(db, tenant_id=tenant_id, order_id=order.id)
