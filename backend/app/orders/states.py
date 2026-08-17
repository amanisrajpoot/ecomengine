"""Order state machine profiles and transition rules."""

from __future__ import annotations

from dataclasses import dataclass

TERMINAL_STATUSES = frozenset({"DELIVERED", "CANCELLED", "FAILED", "REFUNDED"})

PROFILE_FOOD_DELIVERY = "FOOD_DELIVERY"
PROFILE_HYPERLOCAL_DELIVERY = "HYPERLOCAL_DELIVERY"
PROFILE_COURIER = "COURIER"
PROFILE_PICKUP_ONLY = "PICKUP_ONLY"


def profile_for_business_type(business_type: str) -> str:
    mapping = {
        "FOOD": PROFILE_FOOD_DELIVERY,
        "GROCERY": PROFILE_HYPERLOCAL_DELIVERY,
        "RETAIL": PROFILE_HYPERLOCAL_DELIVERY,
        "COURIER": PROFILE_COURIER,
    }
    return mapping.get(business_type, PROFILE_FOOD_DELIVERY)


_FOOD_TRANSITIONS: dict[str, set[str]] = {
    "CREATED": {"PAYMENT_PENDING"},
    "PAYMENT_PENDING": {"PAYMENT_CONFIRMED", "CANCELLED"},
    "PAYMENT_CONFIRMED": {"ACCEPTED", "CANCELLED"},
    "ACCEPTED": {"PREPARING", "CANCELLED"},
    "PREPARING": {"READY", "CANCELLED"},
    "READY": {"PICKED_UP", "CANCELLED"},
    "PICKED_UP": {"OUT_FOR_DELIVERY", "CANCELLED"},
    "OUT_FOR_DELIVERY": {"DELIVERED", "CANCELLED"},
}

_HYPERLOCAL_TRANSITIONS: dict[str, set[str]] = {
    "CREATED": {"PAYMENT_PENDING"},
    "PAYMENT_PENDING": {"PAYMENT_CONFIRMED", "CANCELLED"},
    "PAYMENT_CONFIRMED": {"ACCEPTED", "CANCELLED"},
    "ACCEPTED": {"PICKING", "CANCELLED"},
    "PICKING": {"READY", "CANCELLED"},
    "READY": {"PICKED_UP", "CANCELLED"},
    "PICKED_UP": {"OUT_FOR_DELIVERY", "CANCELLED"},
    "OUT_FOR_DELIVERY": {"DELIVERED", "CANCELLED"},
}

_COURIER_TRANSITIONS: dict[str, set[str]] = {
    "CREATED": {"PAYMENT_PENDING"},
    "PAYMENT_PENDING": {"PAYMENT_CONFIRMED", "CANCELLED"},
    "PAYMENT_CONFIRMED": {"PICKUP_ASSIGNED", "CANCELLED"},
    "PICKUP_ASSIGNED": {"PICKED_UP", "CANCELLED"},
    "PICKED_UP": {"IN_TRANSIT", "CANCELLED"},
    "IN_TRANSIT": {"DELIVERED", "CANCELLED"},
}

_PROFILE_TRANSITIONS: dict[str, dict[str, set[str]]] = {
    PROFILE_FOOD_DELIVERY: _FOOD_TRANSITIONS,
    PROFILE_HYPERLOCAL_DELIVERY: _HYPERLOCAL_TRANSITIONS,
    PROFILE_COURIER: _COURIER_TRANSITIONS,
    PROFILE_PICKUP_ONLY: {
        "CREATED": {"PAYMENT_PENDING"},
        "PAYMENT_PENDING": {"PAYMENT_CONFIRMED", "CANCELLED"},
        "PAYMENT_CONFIRMED": {"READY", "CANCELLED"},
        "READY": {"DELIVERED", "CANCELLED"},
    },
}


@dataclass(frozen=True)
class StateMachine:
    profile: str
    transitions: dict[str, set[str]]

    def can_transition(self, from_status: str, to_status: str) -> bool:
        if from_status in TERMINAL_STATUSES:
            return False
        if to_status == "CANCELLED" and from_status not in TERMINAL_STATUSES:
            return True
        allowed = self.transitions.get(from_status, set())
        return to_status in allowed

    def initial_status(self) -> str:
        return "CREATED"


class StateMachineRegistry:
    def get(self, profile: str) -> StateMachine:
        transitions = _PROFILE_TRANSITIONS.get(profile)
        if transitions is None:
            transitions = _FOOD_TRANSITIONS
        return StateMachine(profile=profile, transitions=transitions)


registry = StateMachineRegistry()
