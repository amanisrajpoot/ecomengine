"""Fulfillment types and status machine (logistics stay in Phase 12 delivery)."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.errors import AppError

FULFILLMENT_TYPES = frozenset(
    {"DELIVERY", "PICKUP", "SELF_PICKUP", "SCHEDULED", "MULTI_STOP"}
)

TERMINAL_STATUSES = frozenset({"COMPLETED", "CANCELLED", "FAILED"})


@dataclass(frozen=True)
class Transition:
    to_status: str
    actors: frozenset[str] = field(default_factory=lambda: frozenset({"system"}))


@dataclass
class FulfillmentStateMachine:
    """Shared fulfillment statuses; type gates some edges."""

    transitions: dict[str, list[Transition]]
    type_extra: dict[str, dict[str, list[Transition]]] = field(default_factory=dict)

    def _edges(self, status: str, fulfillment_type: str) -> list[Transition]:
        edges = list(self.transitions.get(status, []))
        extra = self.type_extra.get(fulfillment_type, {}).get(status, [])
        return edges + list(extra)

    def can_transition(
        self, from_status: str, to_status: str, actor: str, fulfillment_type: str
    ) -> bool:
        if from_status in TERMINAL_STATUSES:
            return False
        for transition in self._edges(from_status, fulfillment_type):
            if transition.to_status == to_status and actor in transition.actors:
                return True
        if to_status == "CANCELLED":
            for transition in self.transitions.get("*", []):
                if transition.to_status == "CANCELLED" and actor in transition.actors:
                    return True
        return False

    def assert_can_transition(
        self, from_status: str, to_status: str, actor: str, fulfillment_type: str
    ) -> None:
        if not self.can_transition(from_status, to_status, actor, fulfillment_type):
            raise AppError(
                "FULFILLMENT_ILLEGAL_TRANSITION",
                f"Cannot move fulfillment from {from_status} to {to_status} as {actor}",
                status_code=409,
                details={
                    "from_status": from_status,
                    "to_status": to_status,
                    "actor": actor,
                    "fulfillment_type": fulfillment_type,
                },
            )


def build_default_machine() -> FulfillmentStateMachine:
    merchantish = frozenset({"merchant", "staff", "system"})
    ops = frozenset({"system", "merchant", "staff", "rider"})
    return FulfillmentStateMachine(
        transitions={
            "PENDING": [
                Transition("ACCEPTED", merchantish),
                Transition("CANCELLED", frozenset({"merchant", "customer", "system"})),
            ],
            "ACCEPTED": [
                Transition("PREPARING", merchantish),
                Transition("READY", merchantish),  # skip prepare (grocery/courier)
                Transition("CANCELLED", frozenset({"merchant", "system"})),
            ],
            "PREPARING": [
                Transition("READY", merchantish),
                Transition("CANCELLED", frozenset({"merchant", "system"})),
            ],
            "READY": [
                # SELF_PICKUP completes at counter; DELIVERY waits for logistics.
                Transition("COMPLETED", merchantish),
                Transition("AWAITING_PICKUP", ops),
                Transition("CANCELLED", frozenset({"merchant", "system"})),
            ],
            "AWAITING_PICKUP": [
                Transition("IN_TRANSIT", frozenset({"system", "rider"})),
                Transition("COMPLETED", frozenset({"system", "rider", "merchant"})),
                Transition("CANCELLED", frozenset({"system", "merchant"})),
            ],
            "IN_TRANSIT": [
                Transition("COMPLETED", frozenset({"system", "rider"})),
                Transition("FAILED", frozenset({"system", "rider"})),
            ],
            "*": [
                Transition("CANCELLED", frozenset({"system"})),
            ],
        },
        type_extra={
            # SELF_PICKUP should not go IN_TRANSIT via normal happy path;
            # READY → COMPLETED is enough. AWAITING_PICKUP still allowed for queue.
            "MULTI_STOP": {
                "READY": [
                    Transition("AWAITING_PICKUP", ops),
                ],
            },
        },
    )


# Order status → fulfillment status when syncing from the order engine.
ORDER_TO_FULFILLMENT: dict[str, str] = {
    "PAYMENT_CONFIRMED": "PENDING",
    "ACCEPTED": "ACCEPTED",
    "PREPARING": "PREPARING",
    "PICKING": "PREPARING",
    "READY": "READY",
    "PICKUP_ASSIGNED": "AWAITING_PICKUP",
    "PICKED_UP": "IN_TRANSIT",
    "OUT_FOR_DELIVERY": "IN_TRANSIT",
    "IN_TRANSIT": "IN_TRANSIT",
    "DELIVERED": "COMPLETED",
    "CANCELLED": "CANCELLED",
    "FAILED": "FAILED",
}


registry = build_default_machine()
