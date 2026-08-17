"""Settlement calculation and lifecycle."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.ledger.models import LedgerEntry
from app.orders.models import Order
from app.settlements.models import Settlement, SettlementLedgerLink
from app.settlements.schemas import SettlementCalculate, SettlementTransition
from app.settlements.states import (
    PARTY_ACCOUNT_MAP,
    PARTY_TYPES,
    can_transition,
)


async def _get_settlement(
    db: AsyncSession, *, tenant_id: uuid.UUID, settlement_id: uuid.UUID
) -> Settlement:
    settlement = await db.scalar(
        select(Settlement).where(
            Settlement.id == settlement_id,
            Settlement.tenant_id == tenant_id,
        )
    )
    if not settlement:
        raise AppError("SETTLEMENT_NOT_FOUND", "Settlement not found", status_code=404)
    return settlement


async def _linked_entry_ids(db: AsyncSession) -> set[uuid.UUID]:
    rows = await db.scalars(select(SettlementLedgerLink.ledger_entry_id))
    return set(rows)


def _net_for_entries(entries: list[LedgerEntry]) -> tuple[int, dict[str, Any]]:
    credits = sum(e.amount_paise for e in entries if e.direction == "CREDIT")
    debits = sum(e.amount_paise for e in entries if e.direction == "DEBIT")
    account = entries[0].account if entries else ""
    report = {
        "by_account": {
            account: {
                "credits_paise": credits,
                "debits_paise": debits,
                "net_paise": credits - debits,
            }
        },
        "ledger_entry_count": len(entries),
        "order_ids": sorted(
            {str(e.order_id) for e in entries if e.order_id is not None}
        ),
    }
    return credits - debits, report


async def _unsettled_entries_for_party(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    party_type: str,
    party_id: uuid.UUID,
    account: str,
    period_start: datetime,
    period_end: datetime,
    linked_ids: set[uuid.UUID],
) -> list[LedgerEntry]:
    stmt = (
        select(LedgerEntry)
        .where(
            LedgerEntry.tenant_id == tenant_id,
            LedgerEntry.account == account,
            LedgerEntry.created_at >= period_start,
            LedgerEntry.created_at < period_end,
        )
        .order_by(LedgerEntry.created_at.asc())
    )
    if linked_ids:
        stmt = stmt.where(LedgerEntry.id.not_in(linked_ids))

    if party_type == "MERCHANT":
        stmt = stmt.join(Order, LedgerEntry.order_id == Order.id).where(
            Order.business_id == party_id
        )
    elif party_type in {"PLATFORM", "DELIVERY_PARTNER"}:
        if party_id != tenant_id:
            raise AppError(
                "INVALID_SETTLEMENT_PARTY",
                f"{party_type} settlements use tenant_id as party_id",
                status_code=400,
            )
    else:
        raise AppError("INVALID_PARTY_TYPE", f"Unknown party type {party_type}", 400)

    return list(await db.scalars(stmt))


async def calculate_settlement(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    payload: SettlementCalculate,
) -> Settlement:
    if payload.party_type not in PARTY_TYPES:
        raise AppError(
            "INVALID_PARTY_TYPE",
            f"party_type must be one of {sorted(PARTY_TYPES)}",
            status_code=400,
        )
    if payload.period_end <= payload.period_start:
        raise AppError(
            "INVALID_SETTLEMENT_PERIOD",
            "period_end must be after period_start",
            status_code=400,
        )

    account = PARTY_ACCOUNT_MAP[payload.party_type]
    linked_ids = await _linked_entry_ids(db)
    entries = await _unsettled_entries_for_party(
        db,
        tenant_id=tenant_id,
        party_type=payload.party_type,
        party_id=payload.party_id,
        account=account,
        period_start=payload.period_start,
        period_end=payload.period_end,
        linked_ids=linked_ids,
    )
    if not entries:
        raise AppError(
            "SETTLEMENT_NO_ENTRIES",
            "No unsettled ledger entries for this party and period",
            status_code=400,
        )

    total_paise, report = _net_for_entries(entries)
    settlement = Settlement(
        tenant_id=tenant_id,
        party_type=payload.party_type,
        party_id=payload.party_id,
        status="CALCULATED",
        period_start=payload.period_start,
        period_end=payload.period_end,
        total_paise=total_paise,
        currency=payload.currency,
        report=report,
    )
    db.add(settlement)
    await db.flush()

    for entry in entries:
        db.add(
            SettlementLedgerLink(
                settlement_id=settlement.id,
                ledger_entry_id=entry.id,
            )
        )

    await db.commit()
    await db.refresh(settlement)
    return settlement


async def get_settlement(
    db: AsyncSession, *, tenant_id: uuid.UUID, settlement_id: uuid.UUID
) -> tuple[Settlement, list[uuid.UUID]]:
    settlement = await _get_settlement(db, tenant_id=tenant_id, settlement_id=settlement_id)
    entry_ids = list(
        await db.scalars(
            select(SettlementLedgerLink.ledger_entry_id).where(
                SettlementLedgerLink.settlement_id == settlement_id
            )
        )
    )
    return settlement, entry_ids


async def list_settlements(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    party_type: str | None = None,
    party_id: uuid.UUID | None = None,
    status: str | None = None,
) -> list[Settlement]:
    stmt = select(Settlement).where(Settlement.tenant_id == tenant_id)
    if party_type:
        stmt = stmt.where(Settlement.party_type == party_type)
    if party_id:
        stmt = stmt.where(Settlement.party_id == party_id)
    if status:
        stmt = stmt.where(Settlement.status == status)
    stmt = stmt.order_by(Settlement.created_at.desc())
    return list(await db.scalars(stmt))


async def list_settlements_for_order(
    db: AsyncSession, *, tenant_id: uuid.UUID, order_id: uuid.UUID
) -> list[Settlement]:
    entry_ids = list(
        await db.scalars(
            select(LedgerEntry.id).where(
                LedgerEntry.tenant_id == tenant_id,
                LedgerEntry.order_id == order_id,
            )
        )
    )
    if not entry_ids:
        return []

    settlement_ids = list(
        await db.scalars(
            select(SettlementLedgerLink.settlement_id).where(
                SettlementLedgerLink.ledger_entry_id.in_(entry_ids)
            )
        )
    )
    if not settlement_ids:
        return []

    stmt = (
        select(Settlement)
        .where(Settlement.tenant_id == tenant_id, Settlement.id.in_(settlement_ids))
        .order_by(Settlement.created_at.desc())
    )
    return list(await db.scalars(stmt))


async def transition_settlement(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    settlement_id: uuid.UUID,
    payload: SettlementTransition,
    actor_user_id: uuid.UUID | None = None,
) -> Settlement:
    _ = actor_user_id
    settlement = await _get_settlement(db, tenant_id=tenant_id, settlement_id=settlement_id)
    if not can_transition(settlement.status, payload.to_status):
        raise AppError(
            "INVALID_SETTLEMENT_TRANSITION",
            f"Cannot transition from {settlement.status} to {payload.to_status}",
            status_code=400,
        )

    settlement.status = payload.to_status
    if payload.reason:
        settlement.report = {
            **settlement.report,
            "last_transition": {
                "to_status": payload.to_status,
                "reason": payload.reason,
                "at": datetime.now(timezone.utc).isoformat(),
            },
        }

    await db.commit()
    await db.refresh(settlement)
    return settlement
