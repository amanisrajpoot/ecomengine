"""ONDC adapter orchestration — calls core services, never imported by core."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.businesses.service import list_businesses
from app.cart.schemas import CartCreate, CartItemCreate
from app.cart.service import add_cart_item, create_cart, recalculate_cart_pricing
from app.catalog.service import list_products, list_variants
from app.orders.schemas import OrderCheckout
from app.orders.service import checkout_from_cart, get_order
from app.payments.gateway import PaymentProvider
from app.payments.schemas import PaymentCreate
from app.payments.service import create_payment_for_order
from app.pricing.schemas import PriceBreakdown

from app.integrations.ondc.mapper import (
    breakdown_to_quote,
    business_to_provider,
    order_to_status_payload,
    variant_to_item,
)
from app.integrations.ondc.schemas import (
    OndcConfirmMessage,
    OndcInitMessage,
    OndcSearchMessage,
    OndcSelectMessage,
    OndcStatusMessage,
)


async def search_catalog(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    message: OndcSearchMessage,
) -> dict:
    businesses = await list_businesses(
        db,
        tenant_id=tenant_id,
        status="ACTIVE",
        business_type=message.business_type,
    )
    providers = []
    items = []
    for business in businesses:
        providers.append(business_to_provider(business).model_dump())
        products = await list_products(
            db,
            tenant_id=tenant_id,
            business_id=business.id,
            active_only=True,
        )
        for product in products:
            variants = await list_variants(
                db,
                tenant_id=tenant_id,
                business_id=business.id,
                product_id=product.id,
                available_only=True,
            )
            for variant in variants:
                items.append(variant_to_item(product, variant).model_dump())
    return {"providers": providers, "items": items}


async def select_items(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    message: OndcSelectMessage,
) -> dict:
    cart = await create_cart(
        db,
        tenant_id=tenant_id,
        customer_id=message.customer_id,
        payload=CartCreate(business_id=message.business_id),
    )
    for line in message.items:
        await add_cart_item(
            db,
            tenant_id=tenant_id,
            cart_id=cart.id,
            customer_id=message.customer_id,
            payload=CartItemCreate(variant_id=line.variant_id, quantity=line.quantity),
        )
    cart, pricing_dict = await recalculate_cart_pricing(
        db,
        tenant_id=tenant_id,
        cart_id=cart.id,
        customer_id=message.customer_id,
    )
    breakdown = PriceBreakdown.model_validate(pricing_dict)
    quote = breakdown_to_quote(cart.id, breakdown)
    return {
        "cart_id": str(cart.id),
        "quote": quote.model_dump(),
        "items": [
            {
                "variant_id": str(i.variant_id),
                "quantity": i.quantity,
                "unit_price_paise": i.unit_price_paise,
            }
            for i in cart.items
        ],
    }


async def init_order(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    message: OndcInitMessage,
) -> dict:
    cart, pricing_dict = await recalculate_cart_pricing(
        db,
        tenant_id=tenant_id,
        cart_id=message.cart_id,
        customer_id=message.customer_id,
    )
    breakdown = PriceBreakdown.model_validate(pricing_dict)
    quote = breakdown_to_quote(cart.id, breakdown)
    return {
        "cart_id": str(cart.id),
        "quote": quote.model_dump(),
        "payment": {
            "type": "ON-ORDER",
            "status": "NOT-PAID",
            "amount_paise": breakdown.total_paise,
            "currency": breakdown.currency,
        },
    }


async def confirm_order(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    message: OndcConfirmMessage,
) -> dict:
    order = await checkout_from_cart(
        db,
        tenant_id=tenant_id,
        customer_id=message.customer_id,
        payload=OrderCheckout(
            cart_id=message.cart_id,
            fulfillment_type=message.fulfillment_type,
        ),
    )
    payment, _ = await create_payment_for_order(
        db,
        tenant_id=tenant_id,
        order_id=order.id,
        customer_id=message.customer_id,
        payload=PaymentCreate(provider=PaymentProvider.COD),
        idempotency_key=f"ondc-{order.id}",
    )
    return {
        "order_id": str(order.id),
        "order_state": order.status,
        "payment_id": str(payment.id),
        "payment_status": payment.status,
        "amount_paise": payment.amount_paise,
    }


async def order_status(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    message: OndcStatusMessage,
) -> dict:
    order = await get_order(db, tenant_id=tenant_id, order_id=message.order_id)
    return order_to_status_payload(order)
