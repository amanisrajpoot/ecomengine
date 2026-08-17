"""Delivery status transitions."""

from __future__ import annotations

TRANSITIONS: dict[str, set[str]] = {
    "PENDING": {"ASSIGNED", "CANCELLED"},
    "ASSIGNED": {"IN_PROGRESS", "CANCELLED"},
    "IN_PROGRESS": {"COMPLETED", "CANCELLED"},
    "COMPLETED": set(),
    "CANCELLED": set(),
}

STOP_TYPES = frozenset({"PICKUP", "DROP"})


def can_transition(from_status: str, to_status: str) -> bool:
    return to_status in TRANSITIONS.get(from_status, set())
