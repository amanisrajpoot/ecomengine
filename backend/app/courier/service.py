"""Courier shipment checkout — creates a shared Order (MULTI_STOP / COURIER profile)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.businesses.service import get_business
from app.cart.service import get_or_create_customer_profile
from app.core.errors import AppError
from app.core.events import event_bus
from app.courier.quote import point_dict, quote_fare
from app.courier.schemas import CourierQuoteRequest, CourierShipmentCreate
from app.orders.models import Order, OrderItem, OrderStatusEvent
from app.orders.service import get_order
from app.payments.schemas import InitiatePaymentBody
from app.payments.service import initiate_payment
from app.taxation.schemas import TaxKind
from app.taxation.service import load_rules_for_calculation
from app.verticals.courier import COURIER_DEFAULT_FULFILLMENT, COURIER_STATE_MACHINE_PROFILE


async def create_shipment(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: CourierShipmentCreate,
) -> tuple[Order, list[OrderItem], list[OrderStatusEvent]]:
    business = await get_business(db, tenant_id=tenant_id, business_id=payload.business_id)
    if business.type != "COURIER":
        raise AppError(
            "NOT_COURIER_BUSINESS",
            "Shipment checkout requires a COURIER business",
            400,
            details={"business_type": business.type},
        )
    if not business.capabilities.get("delivery", True):
        raise AppError("DELIVERY_DISABLED", "Business does not support delivery", 400)

    tax_rules = await load_rules_for_calculation(
        db, tenant_id=tenant_id, kind=TaxKind.CUSTOMER_TRANSACTION.value
    )
    quote = quote_fare(
        CourierQuoteRequest(
            pickup=payload.pickup,
            drop=payload.drop,
            weight_kg=payload.weight_kg,
            vehicle_type=payload.vehicle_type,
            express=payload.express,
            platform_fee_paise=payload.platform_fee_paise,
            business_id=payload.business_id,
        ),
        tax_rules=tax_rules,
    )
    pricing = quote.pricing.model_dump(mode="json")
    pricing["courier"] = {
        "distance_km": quote.distance_km,
        "weight_kg": quote.weight_kg,
        "vehicle_type": quote.vehicle_type,
        "express": quote.express,
        "fare_components": quote.fare_components,
    }

    customer = await get_or_create_customer_profile(
        db, tenant_id=tenant_id, user_id=user_id
    )
    package_meta = {
        "package": {
            "weight_kg": payload.weight_kg,
            "vehicle_type": payload.vehicle_type,
            "express": payload.express,
            "notes": payload.package_notes,
        },
        "pickup": point_dict(payload.pickup),
        "drop": point_dict(payload.drop),
        "created_by": str(user_id),
    }

    order = Order(
        tenant_id=tenant_id,
        customer_id=customer.id,
        business_id=business.id,
        location_id=None,
        cart_id=None,
        status="CREATED",
        state_machine_profile=COURIER_STATE_MACHINE_PROFILE,
        currency="INR",
        pricing_snapshot=pricing,
        fulfillment_type=COURIER_DEFAULT_FULFILLMENT,
        payment_method="COD" if payload.payment_provider == "cod" else "ONLINE",
        placed_at=datetime.now(UTC),
        metadata_json=package_meta,
    )
    db.add(order)
    await db.flush()

    line = quote.pricing.lines[0]
    db.add(
        OrderItem(
            order_id=order.id,
            variant_id=None,
            bundle_id=None,
            name_snapshot=line.name,
            quantity=line.quantity,
            unit_price_paise=line.unit_price_paise,
            modifiers_paise=0,
            addons_snapshot=[],
            metadata_json={
                "kind": "courier_fare",
                "distance_km": quote.distance_km,
                "weight_kg": quote.weight_kg,
                "vehicle_type": quote.vehicle_type,
                "express": quote.express,
                "fare_components": quote.fare_components,
            },
        )
    )
    db.add(
        OrderStatusEvent(
            order_id=order.id,
            from_status=None,
            to_status=order.status,
            actor_user_id=user_id,
            actor_role="customer",
            reason="courier_shipment_checkout",
        )
    )
    await db.commit()
    await db.refresh(order)

    await event_bus.publish(
        "OrderCreated",
        {
            "tenant_id": str(tenant_id),
            "order_id": str(order.id),
            "status": order.status,
            "profile": COURIER_STATE_MACHINE_PROFILE,
        },
    )

    await initiate_payment(
        db,
        tenant_id=tenant_id,
        order_id=order.id,
        payload=InitiatePaymentBody(
            provider=payload.payment_provider,
            return_url=payload.return_url,
            notify_url=payload.notify_url,
            customer_phone=payload.customer_phone,
            customer_email=payload.customer_email,
            idempotency_key=f"courier-{order.id}",
        ),
        actor_user_id=user_id,
    )
    return await get_order(db, tenant_id=tenant_id, order_id=order.id)
