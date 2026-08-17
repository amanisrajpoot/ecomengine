"""Fulfillment type and status rules."""

from __future__ import annotations

FULFILLMENT_TYPES = frozenset(
    {"DELIVERY", "PICKUP", "SELF_PICKUP", "SCHEDULED", "MULTI_STOP"}
)

TRANSITIONS: dict[str, set[str]] = {
    "PENDING": {"ACTIVE", "CANCELLED"},
    "ACTIVE": {"COMPLETED", "CANCELLED"},
    "COMPLETED": set(),
    "CANCELLED": set(),
}


def default_type_for_business(business_type: str) -> str:
    mapping = {
        "FOOD": "DELIVERY",
        "GROCERY": "DELIVERY",
        "RETAIL": "DELIVERY",
        "COURIER": "MULTI_STOP",
    }
    return mapping.get(business_type, "DELIVERY")


def can_transition(from_status: str, to_status: str) -> bool:
    return to_status in TRANSITIONS.get(from_status, set())
