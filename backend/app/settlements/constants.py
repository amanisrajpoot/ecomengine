"""Settlement party types and lifecycle statuses."""

from __future__ import annotations

from enum import StrEnum

from app.ledger.accounts import LedgerAccount


class SettlementPartyType(StrEnum):
    MERCHANT = "MERCHANT"
    RIDER = "RIDER"
    PLATFORM = "PLATFORM"


class SettlementStatus(StrEnum):
    PENDING = "PENDING"
    CALCULATED = "CALCULATED"
    RECONCILED = "RECONCILED"
    APPROVED = "APPROVED"
    PAID = "PAID"


# Accounts aggregated per party when calculating a settlement.
PARTY_ACCOUNTS: dict[str, frozenset[str]] = {
    SettlementPartyType.MERCHANT: frozenset({LedgerAccount.MERCHANT_PAYABLE}),
    SettlementPartyType.RIDER: frozenset({LedgerAccount.RIDER_PAYABLE}),
    SettlementPartyType.PLATFORM: frozenset(
        {
            LedgerAccount.PLATFORM_COMMISSION,
            LedgerAccount.PLATFORM_FEE_REVENUE,
        }
    ),
}

ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    SettlementStatus.PENDING: frozenset({SettlementStatus.CALCULATED}),
    SettlementStatus.CALCULATED: frozenset(
        {SettlementStatus.RECONCILED, SettlementStatus.PENDING}
    ),
    SettlementStatus.RECONCILED: frozenset(
        {SettlementStatus.APPROVED, SettlementStatus.CALCULATED}
    ),
    SettlementStatus.APPROVED: frozenset({SettlementStatus.PAID, SettlementStatus.RECONCILED}),
    SettlementStatus.PAID: frozenset(),
}
