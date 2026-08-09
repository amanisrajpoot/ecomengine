"""Ledger orchestration: post events, query entries, account balances."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.events import event_bus
from app.ledger.accounts import LedgerEventType
from app.ledger.models import LedgerEntry
from app.ledger.postings import build_payment_captured_posting, build_refund_posting
from app.ledger.schemas import (
    AccountBalanceRead,
    LedgerEntryRead,
    LedgerEventRead,
    LedgerPostingRequest,
    ManualAdjustmentBody,
)
from app.orders.models import Order
from app.payments.models import Payment, Refund
from app.taxation.engine import calculate_tax_from_rules
from app.taxation.service import load_rules_for_calculation
from app.tenants.models import Tenant


async def _entries_for_reference(
    db: AsyncSession, *, tenant_id: uuid.UUID, reference_key: str
) -> list[LedgerEntry]:
    return list(
        await db.scalars(
            select(LedgerEntry)
            .where(
                LedgerEntry.tenant_id == tenant_id,
                LedgerEntry.reference_key == reference_key,
            )
            .order_by(LedgerEntry.created_at.asc())
        )
    )


async def post_event(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    posting: LedgerPostingRequest,
    commit: bool = True,
) -> list[LedgerEntry]:
    existing = await _entries_for_reference(
        db, tenant_id=tenant_id, reference_key=posting.reference_key
    )
    if existing:
        return existing

    group_id = uuid.uuid4()
    entries: list[LedgerEntry] = []
    for line in posting.lines:
        entry = LedgerEntry(
            tenant_id=tenant_id,
            order_id=posting.order_id,
            event_group_id=group_id,
            event_type=posting.event_type,
            account=line.account,
            direction=line.direction,
            amount_paise=line.amount_paise,
            currency=posting.currency,
            reference_key=posting.reference_key,
            metadata_json={**(line.metadata or {}), **(posting.metadata or {})},
        )
        db.add(entry)
        entries.append(entry)

    if commit:
        await db.commit()
        for entry in entries:
            await db.refresh(entry)
    else:
        await db.flush()

    await event_bus.publish(
        "LedgerEventPosted",
        {
            "tenant_id": str(tenant_id),
            "event_group_id": str(group_id),
            "event_type": posting.event_type,
            "reference_key": posting.reference_key,
            "order_id": str(posting.order_id) if posting.order_id else None,
        },
    )
    return entries


async def resolve_commission_bps(db: AsyncSession, *, tenant_id: uuid.UUID) -> int:
    settings = get_settings()
    tenant = await db.get(Tenant, tenant_id)
    if tenant and isinstance(tenant.config, dict):
        extra = tenant.config.get("extra") if isinstance(tenant.config.get("extra"), dict) else {}
        if "commission_bps" in (extra or {}):
            try:
                return max(0, int(extra["commission_bps"]))
            except (TypeError, ValueError):
                pass
        if "commission_bps" in tenant.config:
            try:
                return max(0, int(tenant.config["commission_bps"]))
            except (TypeError, ValueError):
                pass
    return settings.ledger_default_commission_bps


async def _commission_gst_paise(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    commission_paise: int,
    jurisdiction: str = "IN-INTRA",
) -> int:
    if commission_paise <= 0:
        return 0
    rules = await load_rules_for_calculation(
        db, tenant_id=tenant_id, kind="PLATFORM_SERVICE"
    )
    result = calculate_tax_from_rules(
        taxable_paise=commission_paise,
        kind="PLATFORM_SERVICE",
        category="COMMISSION",
        jurisdiction=jurisdiction,
        rules=rules,
    )
    return int(result.tax_paise or 0)


async def post_payment_captured(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    order: Order,
    payment: Payment,
    commit: bool = True,
) -> list[LedgerEntry]:
    snapshot = order.pricing_snapshot or {}
    total = int(snapshot.get("total_paise") or 0)
    if total <= 0:
        return []

    commission_bps = await resolve_commission_bps(db, tenant_id=tenant_id)
    goods = max(
        int(snapshot.get("subtotal_paise") or 0) - int(snapshot.get("discount_paise") or 0),
        0,
    )
    commission = (goods * commission_bps) // 10_000
    commission_gst = await _commission_gst_paise(
        db, tenant_id=tenant_id, commission_paise=commission
    )

    posting = build_payment_captured_posting(
        reference_key=f"payment-captured:{payment.id}",
        order_id=order.id,
        pricing_snapshot=snapshot,
        payment_provider=payment.provider,
        payment_id=str(payment.id),
        commission_bps=commission_bps,
        commission_gst_paise=commission_gst,
        currency=order.currency or "INR",
    )
    return await post_event(db, tenant_id=tenant_id, posting=posting, commit=commit)


async def post_payment_refund(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    payment: Payment,
    refund: Refund,
    commit: bool = True,
) -> list[LedgerEntry]:
    if refund.amount_paise <= 0:
        return []
    posting = build_refund_posting(
        reference_key=f"payment-refund:{refund.id}",
        order_id=payment.order_id,
        refund_id=str(refund.id),
        payment_id=str(payment.id),
        amount_paise=refund.amount_paise,
        payment_provider=payment.provider,
        currency=payment.currency or "INR",
    )
    return await post_event(db, tenant_id=tenant_id, posting=posting, commit=commit)


async def post_manual_adjustment(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    payload: ManualAdjustmentBody,
) -> list[LedgerEntry]:
    posting = LedgerPostingRequest(
        event_type=LedgerEventType.MANUAL_ADJUSTMENT,
        reference_key=payload.reference_key,
        order_id=payload.order_id,
        currency=payload.currency,
        lines=payload.lines,
        metadata={**(payload.metadata or {}), "reason": payload.reason},
    )
    return await post_event(db, tenant_id=tenant_id, posting=posting, commit=True)


def _to_event_read(entries: list[LedgerEntry]) -> LedgerEventRead:
    if not entries:
        raise AppError("LEDGER_EVENT_NOT_FOUND", "Ledger event not found", 404)
    debits = sum(e.amount_paise for e in entries if e.direction == "DEBIT")
    credits = sum(e.amount_paise for e in entries if e.direction == "CREDIT")
    first = entries[0]
    return LedgerEventRead(
        event_group_id=first.event_group_id,
        event_type=first.event_type,
        reference_key=first.reference_key,
        order_id=first.order_id,
        currency=first.currency,
        debit_total_paise=debits,
        credit_total_paise=credits,
        entries=[LedgerEntryRead.model_validate(e) for e in entries],
    )


async def list_entries(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    order_id: uuid.UUID | None = None,
    account: str | None = None,
    event_type: str | None = None,
    business_ids: list[uuid.UUID] | None = None,
) -> list[LedgerEntry]:
    stmt: Select[Any] = select(LedgerEntry).where(LedgerEntry.tenant_id == tenant_id)
    if business_ids is not None:
        stmt = stmt.join(Order, LedgerEntry.order_id == Order.id).where(
            Order.business_id.in_(business_ids)
        )
    if order_id:
        stmt = stmt.where(LedgerEntry.order_id == order_id)
    if account:
        stmt = stmt.where(LedgerEntry.account == account)
    if event_type:
        stmt = stmt.where(LedgerEntry.event_type == event_type)
    stmt = stmt.order_by(LedgerEntry.created_at.asc())
    return list(await db.scalars(stmt))


async def get_event_group(
    db: AsyncSession, *, tenant_id: uuid.UUID, event_group_id: uuid.UUID
) -> LedgerEventRead:
    entries = list(
        await db.scalars(
            select(LedgerEntry)
            .where(
                LedgerEntry.tenant_id == tenant_id,
                LedgerEntry.event_group_id == event_group_id,
            )
            .order_by(LedgerEntry.created_at.asc())
        )
    )
    return _to_event_read(entries)


async def account_balances(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    order_id: uuid.UUID | None = None,
    business_ids: list[uuid.UUID] | None = None,
) -> list[AccountBalanceRead]:
    stmt = (
        select(
            LedgerEntry.account,
            LedgerEntry.direction,
            func.coalesce(func.sum(LedgerEntry.amount_paise), 0),
        )
        .where(LedgerEntry.tenant_id == tenant_id)
        .group_by(LedgerEntry.account, LedgerEntry.direction)
    )
    if business_ids is not None:
        stmt = stmt.join(Order, LedgerEntry.order_id == Order.id).where(
            Order.business_id.in_(business_ids)
        )
    if order_id:
        stmt = stmt.where(LedgerEntry.order_id == order_id)
    rows = await db.execute(stmt)
    buckets: dict[str, dict[str, int]] = {}
    for account, direction, total in rows.all():
        bucket = buckets.setdefault(account, {"DEBIT": 0, "CREDIT": 0})
        bucket[str(direction)] = int(total)
    return [
        AccountBalanceRead(
            account=account,
            debit_paise=vals["DEBIT"],
            credit_paise=vals["CREDIT"],
            net_paise=vals["CREDIT"] - vals["DEBIT"],
        )
        for account, vals in sorted(buckets.items())
    ]
