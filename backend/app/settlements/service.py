"""Settlement aggregation from ledger + lifecycle transitions."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.events import event_bus
from app.ledger.models import LedgerEntry
from app.orders.models import Order
from app.payments.models import Payment, Refund
from app.settlements.constants import (
    ALLOWED_TRANSITIONS,
    PARTY_ACCOUNTS,
    SettlementPartyType,
    SettlementStatus,
)
from app.settlements.models import Settlement, SettlementLedgerLink
from app.settlements.schemas import SettlementCreate, SettlementRead


def _net_from_entries(entries: list[LedgerEntry]) -> int:
    """Payable/revenue net: credits increase entitlement, debits reduce it."""
    credit = sum(e.amount_paise for e in entries if e.direction == "CREDIT")
    debit = sum(e.amount_paise for e in entries if e.direction == "DEBIT")
    return credit - debit


async def _get_settlement(
    db: AsyncSession, *, tenant_id: uuid.UUID, settlement_id: uuid.UUID
) -> Settlement:
    settlement = await db.scalar(
        select(Settlement).where(
            Settlement.id == settlement_id, Settlement.tenant_id == tenant_id
        )
    )
    if not settlement:
        raise AppError("SETTLEMENT_NOT_FOUND", "Settlement not found", 404)
    return settlement


async def _link_ids(db: AsyncSession, settlement_id: uuid.UUID) -> list[uuid.UUID]:
    return list(
        await db.scalars(
            select(SettlementLedgerLink.ledger_entry_id).where(
                SettlementLedgerLink.settlement_id == settlement_id
            )
        )
    )


async def to_read(db: AsyncSession, settlement: Settlement) -> SettlementRead:
    ids = await _link_ids(db, settlement.id)
    return SettlementRead(
        id=settlement.id,
        tenant_id=settlement.tenant_id,
        party_type=settlement.party_type,
        party_id=settlement.party_id,
        status=settlement.status,
        period_start=settlement.period_start,
        period_end=settlement.period_end,
        total_paise=settlement.total_paise,
        currency=settlement.currency,
        report=settlement.report or {},
        created_at=settlement.created_at,
        updated_at=settlement.updated_at,
        ledger_entry_ids=ids,
    )


async def create_settlement(
    db: AsyncSession, *, tenant_id: uuid.UUID, payload: SettlementCreate
) -> Settlement:
    if payload.period_end <= payload.period_start:
        raise AppError(
            "INVALID_SETTLEMENT_PERIOD",
            "period_end must be after period_start",
            400,
        )
    if payload.party_type not in PARTY_ACCOUNTS:
        raise AppError("INVALID_PARTY_TYPE", "Unsupported settlement party_type", 400)

    settlement = Settlement(
        tenant_id=tenant_id,
        party_type=payload.party_type,
        party_id=payload.party_id,
        status=SettlementStatus.PENDING,
        period_start=payload.period_start,
        period_end=payload.period_end,
        total_paise=0,
        currency=payload.currency,
        report={},
    )
    db.add(settlement)
    await db.commit()
    await db.refresh(settlement)
    await event_bus.publish(
        "SettlementCreated",
        {
            "tenant_id": str(tenant_id),
            "settlement_id": str(settlement.id),
            "party_type": settlement.party_type,
            "party_id": str(settlement.party_id),
        },
    )
    return settlement


async def list_settlements(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    party_type: str | None = None,
    party_id: uuid.UUID | None = None,
    party_ids: list[uuid.UUID] | None = None,
    status: str | None = None,
) -> list[Settlement]:
    stmt = select(Settlement).where(Settlement.tenant_id == tenant_id)
    if party_type:
        stmt = stmt.where(Settlement.party_type == party_type)
    if party_id:
        stmt = stmt.where(Settlement.party_id == party_id)
    if party_ids:
        stmt = stmt.where(Settlement.party_id.in_(party_ids))
    if status:
        stmt = stmt.where(Settlement.status == status)
    stmt = stmt.order_by(Settlement.created_at.desc())
    return list(await db.scalars(stmt))


async def get_settlement(
    db: AsyncSession, *, tenant_id: uuid.UUID, settlement_id: uuid.UUID
) -> SettlementRead:
    settlement = await _get_settlement(db, tenant_id=tenant_id, settlement_id=settlement_id)
    return await to_read(db, settlement)


async def _already_linked_entry_ids(db: AsyncSession, entry_ids: list[uuid.UUID]) -> set[uuid.UUID]:
    if not entry_ids:
        return set()
    rows = await db.scalars(
        select(SettlementLedgerLink.ledger_entry_id).where(
            SettlementLedgerLink.ledger_entry_id.in_(entry_ids)
        )
    )
    return set(rows)


async def _candidate_entries(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    settlement: Settlement,
) -> list[LedgerEntry]:
    accounts = PARTY_ACCOUNTS[settlement.party_type]
    stmt = (
        select(LedgerEntry)
        .where(
            LedgerEntry.tenant_id == tenant_id,
            LedgerEntry.account.in_(accounts),
            LedgerEntry.created_at >= settlement.period_start,
            LedgerEntry.created_at < settlement.period_end,
        )
        .order_by(LedgerEntry.created_at.asc())
    )

    if settlement.party_type == SettlementPartyType.MERCHANT:
        stmt = (
            select(LedgerEntry)
            .join(Order, Order.id == LedgerEntry.order_id)
            .where(
                LedgerEntry.tenant_id == tenant_id,
                LedgerEntry.account.in_(accounts),
                LedgerEntry.created_at >= settlement.period_start,
                LedgerEntry.created_at < settlement.period_end,
                Order.business_id == settlement.party_id,
            )
            .order_by(LedgerEntry.created_at.asc())
        )
    elif settlement.party_type == SettlementPartyType.PLATFORM:
        # Platform party_id is the tenant itself (convention).
        if settlement.party_id != tenant_id:
            raise AppError(
                "PLATFORM_PARTY_MISMATCH",
                "PLATFORM settlements must use party_id = tenant_id",
                400,
            )
    elif settlement.party_type == SettlementPartyType.RIDER:
        # Until delivery assignment (Phase 12), RIDER settlements aggregate all
        # RIDER_PAYABLE in the period for the given party_id bucket.
        # Entries may carry metadata.rider_party_id later; V1 uses open pool
        # filtered only when metadata contains matching party.
        entries = list(await db.scalars(stmt))
        filtered: list[LedgerEntry] = []
        for entry in entries:
            meta = entry.metadata_json or {}
            rid = meta.get("rider_party_id") or meta.get("party_id")
            if rid is None or str(rid) == str(settlement.party_id):
                filtered.append(entry)
        return filtered

    return list(await db.scalars(stmt))


async def calculate_settlement(
    db: AsyncSession, *, tenant_id: uuid.UUID, settlement_id: uuid.UUID
) -> SettlementRead:
    settlement = await _get_settlement(db, tenant_id=tenant_id, settlement_id=settlement_id)
    if settlement.status not in {SettlementStatus.PENDING, SettlementStatus.CALCULATED}:
        raise AppError(
            "SETTLEMENT_NOT_CALCULABLE",
            f"Cannot calculate settlement in status {settlement.status}",
            409,
        )

    # Clear prior links when recalculating from CALCULATED.
    if settlement.status == SettlementStatus.CALCULATED:
        existing_links = list(
            await db.scalars(
                select(SettlementLedgerLink).where(
                    SettlementLedgerLink.settlement_id == settlement.id
                )
            )
        )
        for link in existing_links:
            await db.delete(link)
        await db.flush()

    candidates = await _candidate_entries(db, tenant_id=tenant_id, settlement=settlement)
    candidate_ids = [e.id for e in candidates]
    linked_elsewhere = await _already_linked_entry_ids(db, candidate_ids)
    includable = [e for e in candidates if e.id not in linked_elsewhere]

    for entry in includable:
        db.add(
            SettlementLedgerLink(settlement_id=settlement.id, ledger_entry_id=entry.id)
        )

    total = _net_from_entries(includable)
    by_account: dict[str, dict[str, int]] = {}
    order_ids: set[str] = set()
    for entry in includable:
        bucket = by_account.setdefault(entry.account, {"debit_paise": 0, "credit_paise": 0})
        if entry.direction == "DEBIT":
            bucket["debit_paise"] += entry.amount_paise
        else:
            bucket["credit_paise"] += entry.amount_paise
        if entry.order_id:
            order_ids.add(str(entry.order_id))

    settlement.total_paise = total
    settlement.status = SettlementStatus.CALCULATED
    settlement.report = {
        **(settlement.report or {}),
        "calculated": {
            "entry_count": len(includable),
            "skipped_already_settled": len(linked_elsewhere),
            "by_account": {
                acct: {
                    **vals,
                    "net_paise": vals["credit_paise"] - vals["debit_paise"],
                }
                for acct, vals in by_account.items()
            },
            "order_ids": sorted(order_ids),
            "total_paise": total,
        },
    }
    await db.commit()
    await db.refresh(settlement)
    await event_bus.publish(
        "SettlementCalculated",
        {
            "tenant_id": str(tenant_id),
            "settlement_id": str(settlement.id),
            "total_paise": total,
        },
    )
    return await to_read(db, settlement)


async def reconcile_settlement(
    db: AsyncSession, *, tenant_id: uuid.UUID, settlement_id: uuid.UUID
) -> SettlementRead:
    settlement = await _get_settlement(db, tenant_id=tenant_id, settlement_id=settlement_id)
    if settlement.status != SettlementStatus.CALCULATED:
        raise AppError(
            "SETTLEMENT_NOT_RECONCILABLE",
            f"Cannot reconcile settlement in status {settlement.status}",
            409,
        )

    entry_ids = await _link_ids(db, settlement.id)
    order_ids: list[uuid.UUID] = []
    if entry_ids:
        order_ids = list(
            {
                oid
                for oid in await db.scalars(
                    select(LedgerEntry.order_id).where(
                        LedgerEntry.id.in_(entry_ids), LedgerEntry.order_id.is_not(None)
                    )
                )
                if oid is not None
            }
        )

    payments_total = 0
    refunds_total = 0
    if order_ids:
        payments_total = int(
            (
                await db.scalar(
                    select(func.coalesce(func.sum(Payment.amount_paise), 0)).where(
                        Payment.tenant_id == tenant_id,
                        Payment.order_id.in_(order_ids),
                        Payment.status.in_(("CAPTURED", "AUTHORIZED")),
                    )
                )
            )
            or 0
        )
        refunds_total = int(
            (
                await db.scalar(
                    select(func.coalesce(func.sum(Refund.amount_paise), 0)).where(
                        Refund.tenant_id == tenant_id,
                        Refund.order_id.in_(order_ids),
                        Refund.status == "REFUNDED",
                    )
                )
            )
            or 0
        )

    # Ledger cash/receivable nets for the same orders (not necessarily linked).
    ledger_cash_net = 0
    if order_ids:
        cash_entries = list(
            await db.scalars(
                select(LedgerEntry).where(
                    LedgerEntry.tenant_id == tenant_id,
                    LedgerEntry.order_id.in_(order_ids),
                    LedgerEntry.account.in_(("PLATFORM_CASH", "CUSTOMER_RECEIVABLE")),
                )
            )
        )
        ledger_cash_net = _net_from_entries(cash_entries)

    expected_net = payments_total - refunds_total
    # For cash accounts, debit increases cash (inflow); net_from_entries is credit-debit,
    # so cash inflow shows as negative. Flip for comparison.
    ledger_inflow = -ledger_cash_net
    matched = ledger_inflow == expected_net

    settlement.status = SettlementStatus.RECONCILED
    settlement.report = {
        **(settlement.report or {}),
        "reconcile": {
            "order_count": len(order_ids),
            "payments_total_paise": payments_total,
            "refunds_total_paise": refunds_total,
            "expected_net_paise": expected_net,
            "ledger_cash_inflow_paise": ledger_inflow,
            "matched": matched,
        },
    }
    await db.commit()
    await db.refresh(settlement)
    await event_bus.publish(
        "SettlementReconciled",
        {
            "tenant_id": str(tenant_id),
            "settlement_id": str(settlement.id),
            "matched": matched,
        },
    )
    return await to_read(db, settlement)


async def _transition(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    settlement_id: uuid.UUID,
    to_status: str,
    event_name: str,
    reason: str | None = None,
) -> SettlementRead:
    settlement = await _get_settlement(db, tenant_id=tenant_id, settlement_id=settlement_id)
    allowed = ALLOWED_TRANSITIONS.get(settlement.status, frozenset())
    if to_status not in allowed:
        raise AppError(
            "SETTLEMENT_ILLEGAL_TRANSITION",
            f"Cannot move settlement from {settlement.status} to {to_status}",
            409,
            details={"from": settlement.status, "to": to_status},
        )
    previous = settlement.status
    settlement.status = to_status
    settlement.report = {
        **(settlement.report or {}),
        "last_transition": {
            "from": previous,
            "to": to_status,
            "reason": reason,
        },
    }
    await db.commit()
    await db.refresh(settlement)
    await event_bus.publish(
        event_name,
        {
            "tenant_id": str(tenant_id),
            "settlement_id": str(settlement.id),
            "from_status": previous,
            "to_status": to_status,
        },
    )
    return await to_read(db, settlement)


async def approve_settlement(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    settlement_id: uuid.UUID,
    reason: str | None = None,
) -> SettlementRead:
    return await _transition(
        db,
        tenant_id=tenant_id,
        settlement_id=settlement_id,
        to_status=SettlementStatus.APPROVED,
        event_name="SettlementApproved",
        reason=reason,
    )


async def mark_settlement_paid(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    settlement_id: uuid.UUID,
    reason: str | None = None,
) -> SettlementRead:
    return await _transition(
        db,
        tenant_id=tenant_id,
        settlement_id=settlement_id,
        to_status=SettlementStatus.PAID,
        event_name="SettlementPaid",
        reason=reason,
    )


async def list_settlements_for_order(
    db: AsyncSession, *, tenant_id: uuid.UUID, order_id: uuid.UUID
) -> list[SettlementRead]:
    settlement_ids = list(
        await db.scalars(
            select(SettlementLedgerLink.settlement_id)
            .join(LedgerEntry, LedgerEntry.id == SettlementLedgerLink.ledger_entry_id)
            .where(LedgerEntry.tenant_id == tenant_id, LedgerEntry.order_id == order_id)
            .distinct()
        )
    )
    if not settlement_ids:
        return []
    settlements = list(
        await db.scalars(
            select(Settlement)
            .where(Settlement.tenant_id == tenant_id, Settlement.id.in_(settlement_ids))
            .order_by(Settlement.created_at.desc())
        )
    )
    return [await to_read(db, s) for s in settlements]
