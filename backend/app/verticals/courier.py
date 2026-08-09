"""Thin Courier vertical config — package pickup/drop on shared engines."""

from __future__ import annotations

from app.businesses.schemas import BusinessCapabilities, BusinessType

COURIER_TYPES = frozenset({BusinessType.COURIER.value})

COURIER_CAPABILITIES = BusinessCapabilities(
    catalog=False,
    inventory=False,
    addons=False,
    delivery=True,
    scheduledOrders=True,
)

COURIER_STATE_MACHINE_PROFILE = "COURIER"
COURIER_DEFAULT_FULFILLMENT = "MULTI_STOP"

GOLDEN_PATH_STEPS = (
    "quote_by_distance_weight_vehicle",
    "checkout_pay",
    "assign_rider",
    "pickup",
    "in_transit",
    "pod_delivered",
    "ledger_and_settlement",
)
