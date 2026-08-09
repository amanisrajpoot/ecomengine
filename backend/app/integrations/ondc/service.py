"""ONDC BPP adapter services — search/select/init/confirm/status/cancel."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cart.schemas import CartCreate, CartItemCreate
from app.cart.service import add_item, create_cart
from app.catalog import service as catalog_service
from app.core.errors import AppError
from app.identity.models import CustomerProfile, User, UserRoleBinding
from app.identity.rbac import Role
from app.integrations.ondc.mapper import (
    build_catalog,
    build_order_quote,
    map_order_state,
    offer_id,
    parse_offer_id,
    parse_provider_id,
    provider_id,
)
from app.integrations.ondc.models import OndcSession
from app.integrations.ondc.schemas import BecknContext, BecknRequest, BecknResponse
from app.locations.discovery import discover_nearby_stores
from app.orders.schemas import CheckoutRequest, OrderTransitionRequest
from app.orders.service import checkout_from_cart, get_order, transition_order


def _reply_context(ctx: BecknContext, action: str) -> BecknContext:
    return ctx.model_copy(
        update={
            "action": action,
            "message_id": str(uuid.uuid4()),
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )


async def _get_or_create_session(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    request: BecknRequest,
) -> OndcSession:
    ctx = request.context
    session = await db.scalar(
        select(OndcSession).where(
            OndcSession.tenant_id == tenant_id,
            OndcSession.transaction_id == ctx.transaction_id,
        )
    )
    if session:
        session.context_json = ctx.model_dump(mode="json")
        session.bap_id = ctx.bap_id
        session.bap_uri = ctx.bap_uri
        session.bpp_id = ctx.bpp_id
        await db.commit()
        await db.refresh(session)
        return session
    session = OndcSession(
        tenant_id=tenant_id,
        transaction_id=ctx.transaction_id,
        bap_id=ctx.bap_id,
        bap_uri=ctx.bap_uri,
        bpp_id=ctx.bpp_id,
        stage="SEARCH",
        context_json=ctx.model_dump(mode="json"),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


def _parse_gps(message: dict[str, Any]) -> tuple[float, float]:
    intent = message.get("intent") or {}
    fulfillment = intent.get("fulfillment") or {}
    end = fulfillment.get("end") or fulfillment.get("start") or {}
    location = end.get("location") or {}
    gps = location.get("gps") or intent.get("fulfillment", {}).get("end", {}).get("location", {}).get("gps")
    if not gps or "," not in str(gps):
        raise AppError("ONDc_GPS_REQUIRED", "intent.fulfillment.end.location.gps is required", 400)
    lat_s, lng_s = str(gps).split(",", 1)
    return float(lat_s.strip()), float(lng_s.strip())


async def _get_or_create_ondc_customer(
    db: AsyncSession, *, tenant_id: uuid.UUID, phone: str
) -> User:
    user = await db.scalar(
        select(User).where(User.phone == phone, User.tenant_id == tenant_id)
    )
    if user:
        return user
    user = User(phone=phone, tenant_id=tenant_id, status="ACTIVE", display_name="ONDC Buyer")
    db.add(user)
    await db.flush()
    db.add(
        UserRoleBinding(
            user_id=user.id,
            tenant_id=tenant_id,
            business_id=None,
            role=Role.CUSTOMER.value,
        )
    )
    db.add(CustomerProfile(tenant_id=tenant_id, user_id=user.id, display_name="ONDC Buyer"))
    await db.commit()
    await db.refresh(user)
    return user


async def handle_search(
    db: AsyncSession, *, tenant_id: uuid.UUID, request: BecknRequest
) -> BecknResponse:
    lat, lng = _parse_gps(request.message)
    await _get_or_create_session(db, tenant_id=tenant_id, request=request)
    stores = await discover_nearby_stores(db, tenant_id=tenant_id, lat=lat, lng=lng, radius_km=8.0)
    catalog_by_business: dict[uuid.UUID, list] = {}
    for store in stores:
        products = await catalog_service.list_products(
            db, tenant_id=tenant_id, business_id=store.business_id, active_only=True
        )
        rows: list = []
        for product in products:
            variants = await catalog_service.list_variants(
                db, tenant_id=tenant_id, business_id=store.business_id, product_id=product.id
            )
            rows.append((product, variants))
        catalog_by_business[store.business_id] = rows
    catalog = build_catalog(stores, catalog_by_business=catalog_by_business)
    return BecknResponse(context=_reply_context(request.context, "on_search"), message=catalog)


async def handle_select(
    db: AsyncSession, *, tenant_id: uuid.UUID, request: BecknRequest
) -> BecknResponse:
    session = await _get_or_create_session(db, tenant_id=tenant_id, request=request)
    order_msg = request.message.get("order") or {}
    provider_raw = (order_msg.get("provider") or {}).get("id")
    if not provider_raw:
        raise AppError("ONDc_PROVIDER_REQUIRED", "order.provider.id is required", 400)
    business_id, location_id = parse_provider_id(provider_raw)
    selected: list[dict[str, Any]] = []
    for item in order_msg.get("items") or []:
        offer = item.get("id")
        if not offer:
            continue
        _, _, variant_id = parse_offer_id(offer)
        selected.append(
            {
                "offer_id": offer,
                "variant_id": str(variant_id),
                "quantity": int((item.get("quantity") or {}).get("count", 1)),
                "provider_id": provider_raw,
            }
        )
    if not selected:
        raise AppError("ONDc_ITEMS_REQUIRED", "order.items is required", 400)
    session.stage = "SELECT"
    session.business_id = business_id
    session.location_id = location_id
    session.selected_items = selected
    await db.commit()
    return BecknResponse(
        context=_reply_context(request.context, "on_select"),
        message={"order": order_msg},
    )


async def handle_init(
    db: AsyncSession, *, tenant_id: uuid.UUID, request: BecknRequest
) -> BecknResponse:
    session = await _get_or_create_session(db, tenant_id=tenant_id, request=request)
    if not session.business_id or not session.location_id or not session.selected_items:
        raise AppError("ONDc_SESSION_INCOMPLETE", "Run select before init", 409)
    order_msg = request.message.get("order") or {}
    billing = order_msg.get("billing") or {}
    phone = billing.get("phone") or order_msg.get("fulfillment", {}).get("end", {}).get("contact", {}).get("phone")
    if phone:
        session.customer_phone = str(phone)
    user = await _get_or_create_ondc_customer(
        db, tenant_id=tenant_id, phone=session.customer_phone or "9999999999"
    )
    if not session.cart_id:
        cart = await create_cart(
            db,
            tenant_id=tenant_id,
            user_id=user.id,
            payload=CartCreate(
                business_id=session.business_id,
                location_id=session.location_id,
            ),
        )
        session.cart_id = cart.id
        for line in session.selected_items:
            await add_item(
                db,
                tenant_id=tenant_id,
                cart_id=cart.id,
                payload=CartItemCreate(
                    variant_id=uuid.UUID(line["variant_id"]),
                    quantity=line["quantity"],
                ),
            )
    session.stage = "INIT"
    await db.commit()

    from app.cart.service import get_cart

    cart, cart_items = await get_cart(db, tenant_id=tenant_id, cart_id=session.cart_id)
    _ = cart_items
    quote = {
        "order": {
            "provider": {"id": provider_id(session.business_id, session.location_id)},
            "items": [
                {
                    "id": line["offer_id"],
                    "quantity": {"count": line["quantity"]},
                }
                for line in session.selected_items
            ],
            "quote": {
                "price": {
                    "currency": "INR",
                    "value": f"{cart.pricing_snapshot.get('total_paise', 0) / 100:.2f}",
                }
            },
            "payment": {"type": "ON-ORDER"},
        }
    }
    return BecknResponse(context=_reply_context(request.context, "on_init"), message=quote)


async def handle_confirm(
    db: AsyncSession, *, tenant_id: uuid.UUID, request: BecknRequest
) -> BecknResponse:
    session = await _get_or_create_session(db, tenant_id=tenant_id, request=request)
    if not session.cart_id:
        raise AppError("ONDc_SESSION_INCOMPLETE", "Run init before confirm", 409)
    user = await _get_or_create_ondc_customer(
        db, tenant_id=tenant_id, phone=session.customer_phone or "9999999999"
    )
    order, items, _events = await checkout_from_cart(
        db,
        tenant_id=tenant_id,
        user_id=user.id,
        payload=CheckoutRequest(
            cart_id=session.cart_id,
            payment_provider="cod",
            customer_phone=session.customer_phone,
        ),
    )
    order.metadata_json = {
        **(order.metadata_json or {}),
        "channel": "ondc",
        "ondc_transaction_id": session.transaction_id,
        "ondc_customer_phone": session.customer_phone,
    }
    for item, line in zip(items, session.selected_items, strict=False):
        item.metadata_json = {**(item.metadata_json or {}), "ondc_offer_id": line["offer_id"]}
    session.order_id = order.id
    session.stage = "CONFIRM"
    await db.commit()
    provider = provider_id(session.business_id, session.location_id)
    return BecknResponse(
        context=_reply_context(request.context, "on_confirm"),
        message=build_order_quote(order=order, items=items, provider=provider),
    )


async def handle_status(
    db: AsyncSession, *, tenant_id: uuid.UUID, request: BecknRequest
) -> BecknResponse:
    session = await _get_or_create_session(db, tenant_id=tenant_id, request=request)
    order_id_raw = (request.message.get("order_id") or request.message.get("order", {}).get("id"))
    order_id = session.order_id
    if order_id_raw:
        try:
            order_id = uuid.UUID(str(order_id_raw))
        except ValueError:
            pass
    if not order_id:
        raise AppError("ONDc_ORDER_NOT_FOUND", "No order linked to this transaction", 404)
    order, _items, _events = await get_order(db, tenant_id=tenant_id, order_id=order_id)
    provider = (
        provider_id(session.business_id, session.location_id)
        if session.business_id and session.location_id
        else None
    )
    return BecknResponse(
        context=_reply_context(request.context, "on_status"),
        message={
            "order": {
                "id": str(order.id),
                "state": map_order_state(order.status),
                "provider": {"id": provider},
            }
        },
    )


async def handle_cancel(
    db: AsyncSession, *, tenant_id: uuid.UUID, request: BecknRequest
) -> BecknResponse:
    session = await _get_or_create_session(db, tenant_id=tenant_id, request=request)
    if not session.order_id:
        raise AppError("ONDc_ORDER_NOT_FOUND", "No order to cancel", 404)
    user = await _get_or_create_ondc_customer(
        db, tenant_id=tenant_id, phone=session.customer_phone or "9999999999"
    )
    order, _items, _events = await transition_order(
        db,
        tenant_id=tenant_id,
        order_id=session.order_id,
        payload=OrderTransitionRequest(to_status="CANCELLED", actor="customer", reason="ondc_cancel"),
        actor_user_id=user.id,
    )
    session.stage = "CANCEL"
    await db.commit()
    return BecknResponse(
        context=_reply_context(request.context, "on_cancel"),
        message={"order": {"id": str(order.id), "state": map_order_state(order.status)}},
    )
