"""Thin Hyperlocal vertical config — GROCERY/RETAIL on shared engines."""

from __future__ import annotations

from app.businesses.schemas import BusinessCapabilities, BusinessType

HYPERLOCAL_TYPES = frozenset({BusinessType.GROCERY.value, BusinessType.RETAIL.value})

HYPERLOCAL_CAPABILITIES = BusinessCapabilities(
    catalog=True,
    inventory=True,
    addons=False,
    delivery=True,
    scheduledOrders=True,
)

HYPERLOCAL_STATE_MACHINE_PROFILE = "HYPERLOCAL_DELIVERY"
HYPERLOCAL_DEFAULT_FULFILLMENT = "DELIVERY"

GOLDEN_PATH_STEPS = (
    "discover_nearby_store",
    "catalog_with_inventory",
    "cart_and_price",
    "checkout_pay_reserves_stock",
    "staff_accept_picking_ready",
    "assign_rider_deliver_consumes_stock",
    "ledger_and_settlement",
)
