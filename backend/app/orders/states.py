"""Configurable order state machines — profiles, not hard-coded vertical enums on Order."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.errors import AppError

TERMINAL_STATUSES = frozenset({"DELIVERED", "CANCELLED", "FAILED", "REFUNDED"})


@dataclass(frozen=True)
class Transition:
    to_status: str
    actors: frozenset[str] = field(default_factory=lambda: frozenset({"system"}))


@dataclass
class StateMachine:
    profile: str
    initial_status: str
    transitions: dict[str, list[Transition]]

    def allowed_targets(self, from_status: str) -> list[str]:
        return [t.to_status for t in self.transitions.get(from_status, [])]

    def can_transition(self, from_status: str, to_status: str, actor: str) -> bool:
        if from_status in TERMINAL_STATUSES:
            return False
        for transition in self.transitions.get(from_status, []):
            if transition.to_status == to_status and (
                actor in transition.actors or "system" in transition.actors and actor == "system"
            ):
                return True
        # Broad cancel policy for non-terminal states when actor permitted on wildcard.
        if to_status == "CANCELLED":
            for transition in self.transitions.get("*", []):
                if transition.to_status == "CANCELLED" and actor in transition.actors:
                    return True
        return False

    def assert_can_transition(self, from_status: str, to_status: str, actor: str) -> None:
        if not self.can_transition(from_status, to_status, actor):
            raise AppError(
                "ORDER_ILLEGAL_TRANSITION",
                f"Cannot move from {from_status} to {to_status} as {actor}",
                status_code=409,
                details={
                    "profile": self.profile,
                    "from_status": from_status,
                    "to_status": to_status,
                    "actor": actor,
                    "allowed": self.allowed_targets(from_status),
                },
            )


def _food_delivery() -> StateMachine:
    return StateMachine(
        profile="FOOD_DELIVERY",
        initial_status="CREATED",
        transitions={
            "CREATED": [
                Transition("PAYMENT_PENDING", frozenset({"system", "customer"})),
                Transition("PAYMENT_CONFIRMED", frozenset({"system", "payments"})),  # COD shortcut
                Transition("CANCELLED", frozenset({"customer", "system"})),
            ],
            "PAYMENT_PENDING": [
                Transition("PAYMENT_CONFIRMED", frozenset({"system", "payments"})),
                Transition("CANCELLED", frozenset({"customer", "system"})),
            ],
            "PAYMENT_CONFIRMED": [
                Transition("ACCEPTED", frozenset({"merchant", "system"})),
                Transition("CANCELLED", frozenset({"merchant", "customer", "system"})),
            ],
            "ACCEPTED": [
                Transition("PREPARING", frozenset({"merchant", "system"})),
                Transition("CANCELLED", frozenset({"merchant", "system"})),
            ],
            "PREPARING": [
                Transition("READY", frozenset({"merchant", "system"})),
                Transition("CANCELLED", frozenset({"merchant", "system"})),
            ],
            "READY": [
                Transition("PICKED_UP", frozenset({"rider", "system"})),
                Transition("CANCELLED", frozenset({"merchant", "system"})),
            ],
            "PICKED_UP": [
                Transition("OUT_FOR_DELIVERY", frozenset({"rider", "system"})),
            ],
            "OUT_FOR_DELIVERY": [
                Transition("DELIVERED", frozenset({"rider", "system"})),
            ],
            "*": [
                Transition("CANCELLED", frozenset({"system"})),
            ],
        },
    )


def _hyperlocal_delivery() -> StateMachine:
    return StateMachine(
        profile="HYPERLOCAL_DELIVERY",
        initial_status="CREATED",
        transitions={
            "CREATED": [
                Transition("PAYMENT_PENDING", frozenset({"system", "customer"})),
                Transition("PAYMENT_CONFIRMED", frozenset({"system", "payments"})),
                Transition("CANCELLED", frozenset({"customer", "system"})),
            ],
            "PAYMENT_PENDING": [
                Transition("PAYMENT_CONFIRMED", frozenset({"system", "payments"})),
                Transition("CANCELLED", frozenset({"customer", "system"})),
            ],
            "PAYMENT_CONFIRMED": [
                Transition("ACCEPTED", frozenset({"merchant", "system"})),
                Transition("CANCELLED", frozenset({"merchant", "customer", "system"})),
            ],
            "ACCEPTED": [
                Transition("PICKING", frozenset({"merchant", "staff", "system"})),
                Transition("CANCELLED", frozenset({"merchant", "system"})),
            ],
            "PICKING": [
                Transition("READY", frozenset({"merchant", "staff", "system"})),
                Transition("CANCELLED", frozenset({"merchant", "system"})),
            ],
            "READY": [
                Transition("PICKED_UP", frozenset({"rider", "system"})),
            ],
            "PICKED_UP": [
                Transition("OUT_FOR_DELIVERY", frozenset({"rider", "system"})),
            ],
            "OUT_FOR_DELIVERY": [
                Transition("DELIVERED", frozenset({"rider", "system"})),
            ],
            "*": [
                Transition("CANCELLED", frozenset({"system"})),
            ],
        },
    )


def _courier() -> StateMachine:
    return StateMachine(
        profile="COURIER",
        initial_status="CREATED",
        transitions={
            "CREATED": [
                Transition("PAYMENT_PENDING", frozenset({"system", "customer"})),
                Transition("PAYMENT_CONFIRMED", frozenset({"system", "payments"})),
                Transition("CANCELLED", frozenset({"customer", "system"})),
            ],
            "PAYMENT_PENDING": [
                Transition("PAYMENT_CONFIRMED", frozenset({"system", "payments"})),
                Transition("CANCELLED", frozenset({"customer", "system"})),
            ],
            "PAYMENT_CONFIRMED": [
                Transition("PICKUP_ASSIGNED", frozenset({"system", "rider"})),
                Transition("CANCELLED", frozenset({"customer", "system"})),
            ],
            "PICKUP_ASSIGNED": [
                Transition("PICKED_UP", frozenset({"rider", "system"})),
                Transition("CANCELLED", frozenset({"system"})),
            ],
            "PICKED_UP": [
                Transition("IN_TRANSIT", frozenset({"rider", "system"})),
            ],
            "IN_TRANSIT": [
                Transition("DELIVERED", frozenset({"rider", "system"})),
            ],
            "*": [
                Transition("CANCELLED", frozenset({"system"})),
            ],
        },
    )


class StateMachineRegistry:
    def __init__(self) -> None:
        self._profiles: dict[str, StateMachine] = {
            "FOOD_DELIVERY": _food_delivery(),
            "HYPERLOCAL_DELIVERY": _hyperlocal_delivery(),
            "COURIER": _courier(),
        }

    def get(self, profile: str) -> StateMachine:
        machine = self._profiles.get(profile)
        if not machine:
            raise AppError(
                "UNKNOWN_STATE_MACHINE",
                f"Unknown state machine profile: {profile}",
                status_code=400,
            )
        return machine

    def profile_for_business_type(self, business_type: str | None) -> str:
        mapping = {
            "FOOD": "FOOD_DELIVERY",
            "GROCERY": "HYPERLOCAL_DELIVERY",
            "RETAIL": "HYPERLOCAL_DELIVERY",
            "COURIER": "COURIER",
        }
        return mapping.get((business_type or "FOOD").upper(), "FOOD_DELIVERY")


registry = StateMachineRegistry()
