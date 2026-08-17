"""Settlement lifecycle transitions."""

from __future__ import annotations

TRANSITIONS: dict[str, set[str]] = {
    "PENDING": {"CALCULATED"},
    "CALCULATED": {"RECONCILED"},
    "RECONCILED": {"APPROVED"},
    "APPROVED": {"PAID"},
    "PAID": set(),
}

PARTY_TYPES = frozenset({"MERCHANT", "DELIVERY_PARTNER", "PLATFORM"})

PARTY_ACCOUNT_MAP: dict[str, str] = {
    "MERCHANT": "MERCHANT_PAYABLE",
    "DELIVERY_PARTNER": "DELIVERY_PAYABLE",
    "PLATFORM": "PLATFORM_REVENUE",
}


def can_transition(from_status: str, to_status: str) -> bool:
    return to_status in TRANSITIONS.get(from_status, set())
