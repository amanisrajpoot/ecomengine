"""Ledger posting and query service."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.ledger.models import LedgerEntry


def _pricing_parts(pricing_snapshot: dict) -> tuple[list[tuple[str, int]], int]:
    subtotal = int(pricing_snapshot.get("subtotal_paise", 0))
    discount = int(pricing_snapshot.get("discount_paise", 0))
    delivery = int(pricing_snapshot.get("delivery_fee_paise", 0))
    platform = int(pricing_snapshot.get("platform_fee_paise", 0))
    other = int(pricing_snapshot.get("other_fees_paise", 0))
    tax = int(pricing_snapshot.get("tax_paise", 0))
    total = int(pricing_snapshot.get("total_paise", 0))

    merchant = subtotal - discount
    platform_rev = platform + other
    credit_parts = [
        ("MERCHANT_PAYABLE", merchant),
        ("TAX_LIABILITY", tax),
        ("PLATFORM_REVENUE", platform_rev),
        ("DELIVERY_PAYABLE", delivery),
    ]
    credit_sum = sum(amount for _, amount in credit_parts)
    if credit_sum != total:
        raise AppError(
            "LEDGER_UNBALANCED_PRICING",
            f"Pricing snapshot credits {credit_sum} != total {total}",
            status_code=400,
        )
    return credit_parts, total


def _scale_credit_parts(
    credit_parts: list[tuple[str, int]], target_paise: int
) -> list[tuple[str, int]]:
    positive = [(account, amount) for account, amount in credit_parts if amount > 0]
    if target_paise <= 0 or not positive:
        return []
    total = sum(amount for _, amount in positive)
    if target_paise == total:
        return positive

    scaled: list[tuple[str, int]] = []
    allocated = 0
    for index, (account, amount) in enumerate(positive):
        if index == len(positive) - 1:
            scaled.append((account, target_paise - allocated))
        else:
            part = (amount * target_paise) // total
            scaled.append((account, part))
            allocated += part
    return scaled


async def _entries_for_group(
    db: AsyncSession, event_group_id: uuid.UUID
) -> list[LedgerEntry]:
    stmt = (
        select(LedgerEntry)
        .where(LedgerEntry.event_group_id == event_group_id)
        .order_by(LedgerEntry.created_at.asc())
    )
    return list(await db.scalars(stmt))


def _build_entries(
    *,
    tenant_id: uuid.UUID,
    order_id: uuid.UUID | None,
    event_group_id: uuid.UUID,
    event_type: str,
    currency: str,
    cash_direction: str,
    cash_amount: int,
    credit_parts: list[tuple[str, int]],
    reverse: bool = False,
    metadata: dict | None = None,
) -> list[LedgerEntry]:
    meta = metadata or {}
    entries: list[LedgerEntry] = []
    entries.append(
        LedgerEntry(
            tenant_id=tenant_id,
            order_id=order_id,
            event_group_id=event_group_id,
            event_type=event_type,
            account="PLATFORM_CASH",
            direction=cash_direction,
            amount_paise=cash_amount,
            currency=currency,
            meta=meta,
        )
    )
    liability_direction = "DEBIT" if reverse else "CREDIT"
    for account, amount in credit_parts:
        if amount <= 0:
            continue
        entries.append(
            LedgerEntry(
                tenant_id=tenant_id,
                order_id=order_id,
                event_group_id=event_group_id,
                event_type=event_type,
                account=account,
                direction=liability_direction,
                amount_paise=amount,
                currency=currency,
                meta=meta,
            )
        )
    return entries


async def post_payment_captured(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    order_id: uuid.UUID,
    payment_id: uuid.UUID,
    pricing_snapshot: dict,
    currency: str,
) -> list[LedgerEntry]:
    existing = await _entries_for_group(db, payment_id)
    if existing:
        return existing

    credit_parts, total = _pricing_parts(pricing_snapshot)
    entries = _build_entries(
        tenant_id=tenant_id,
        order_id=order_id,
        event_group_id=payment_id,
        event_type="PAYMENT_CAPTURED",
        currency=currency,
        cash_direction="DEBIT",
        cash_amount=total,
        credit_parts=credit_parts,
        metadata={"payment_id": str(payment_id)},
    )
    for entry in entries:
        db.add(entry)
    await db.flush()
    return entries


async def post_refund_completed(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    order_id: uuid.UUID,
    refund_id: uuid.UUID,
    payment_id: uuid.UUID,
    refund_amount_paise: int,
    payment_amount_paise: int,
    pricing_snapshot: dict,
    currency: str,
) -> list[LedgerEntry]:
    existing = await _entries_for_group(db, refund_id)
    if existing:
        return existing

    credit_parts, _ = _pricing_parts(pricing_snapshot)
    scaled = _scale_credit_parts(credit_parts, refund_amount_paise)
    if sum(amount for _, amount in scaled) != refund_amount_paise:
        raise AppError(
            "LEDGER_REFUND_ALLOCATION",
            "Refund allocation does not match refund amount",
            status_code=400,
        )

    entries = _build_entries(
        tenant_id=tenant_id,
        order_id=order_id,
        event_group_id=refund_id,
        event_type="REFUND_COMPLETED",
        currency=currency,
        cash_direction="CREDIT",
        cash_amount=refund_amount_paise,
        credit_parts=scaled,
        reverse=True,
        metadata={
            "payment_id": str(payment_id),
            "refund_id": str(refund_id),
            "payment_amount_paise": payment_amount_paise,
        },
    )
    for entry in entries:
        db.add(entry)
    await db.flush()
    return entries


async def list_entries_for_order(
    db: AsyncSession, *, tenant_id: uuid.UUID, order_id: uuid.UUID
) -> list[LedgerEntry]:
    stmt = (
        select(LedgerEntry)
        .where(LedgerEntry.tenant_id == tenant_id, LedgerEntry.order_id == order_id)
        .order_by(LedgerEntry.created_at.asc())
    )
    return list(await db.scalars(stmt))


async def list_entries_for_event_group(
    db: AsyncSession, *, tenant_id: uuid.UUID, event_group_id: uuid.UUID
) -> list[LedgerEntry]:
    stmt = (
        select(LedgerEntry)
        .where(
            LedgerEntry.tenant_id == tenant_id,
            LedgerEntry.event_group_id == event_group_id,
        )
        .order_by(LedgerEntry.created_at.asc())
    )
    return list(await db.scalars(stmt))
