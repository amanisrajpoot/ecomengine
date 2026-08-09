"""Thin Food vertical configuration — no FoodOrder model; uses shared engines."""

from __future__ import annotations

from app.businesses.schemas import BusinessCapabilities, BusinessType

# Food enables menu addons + delivery; inventory stays off by default.
FOOD_CAPABILITIES = BusinessCapabilities(
    catalog=True,
    inventory=False,
    addons=True,
    delivery=True,
    scheduledOrders=False,
)

FOOD_STATE_MACHINE_PROFILE = "FOOD_DELIVERY"
FOOD_BUSINESS_TYPE = BusinessType.FOOD
FOOD_DEFAULT_FULFILLMENT = "DELIVERY"

GOLDEN_PATH_STEPS = (
    "create_food_business",
    "catalog_with_addons",
    "cart_and_price",
    "checkout_pay",
    "merchant_accept_prepare_ready",
    "assign_rider_deliver",
    "ledger_posted",
    "settlement_calculated",
)
