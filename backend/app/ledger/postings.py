"""Pure posting builders — financial event → balanced ledger drafts."""

from __future__ import annotations

import uuid
from typing import Any

from app.ledger.accounts import LedgerAccount, LedgerDirection, LedgerEventType
from app.ledger.schemas import LedgerLineDraft, LedgerPostingRequest


def _line(
    account: str,
    direction: str,
    amount_paise: int,
    **meta: Any,
) -> LedgerLineDraft | None:
    if amount_paise <= 0:
        return None
    return LedgerLineDraft(
        account=account,
        direction=direction,
        amount_paise=amount_paise,
        metadata=meta,
    )


def build_payment_captured_posting(
    *,
    reference_key: str,
    order_id: uuid.UUID,
    pricing_snapshot: dict[str, Any],
    payment_provider: str,
    payment_id: str,
    commission_bps: int,
    commission_gst_paise: int = 0,
    currency: str = "INR",
) -> LedgerPostingRequest:
    """Post order economics when payment is captured (online) or COD-authorized.

    Double-entry (online):
      DEBIT PLATFORM_CASH total
      CREDIT TAX_LIABILITY customer_tax + commission_gst
      CREDIT PLATFORM_FEE_REVENUE platform_fee
      CREDIT RIDER_PAYABLE delivery_fee
      CREDIT PLATFORM_COMMISSION commission
      CREDIT MERCHANT_PAYABLE goods - commission - commission_gst

    COD uses CUSTOMER_RECEIVABLE instead of PLATFORM_CASH.
    """
    subtotal = int(pricing_snapshot.get("subtotal_paise") or 0)
    discount = int(pricing_snapshot.get("discount_paise") or 0)
    delivery = int(pricing_snapshot.get("delivery_fee_paise") or 0)
    platform_fee = int(pricing_snapshot.get("platform_fee_paise") or 0)
    tax = int(pricing_snapshot.get("tax_paise") or 0)
    total = int(pricing_snapshot.get("total_paise") or 0)
    goods = max(subtotal - discount, 0)

    commission = (goods * max(commission_bps, 0)) // 10_000
    if commission > goods:
        commission = goods
    commission_gst = max(0, min(commission_gst_paise, goods - commission))
    merchant = goods - commission - commission_gst
    tax_liability = tax + commission_gst

    cash_account = (
        LedgerAccount.CUSTOMER_RECEIVABLE
        if payment_provider == "cod"
        else LedgerAccount.PLATFORM_CASH
    )

    lines: list[LedgerLineDraft] = []
    for draft in (
        _line(cash_account, LedgerDirection.DEBIT, total, role="gross_receipt"),
        _line(
            LedgerAccount.TAX_LIABILITY,
            LedgerDirection.CREDIT,
            tax_liability,
            role="tax_liability",
            customer_tax_paise=tax,
            commission_gst_paise=commission_gst,
        ),
        _line(
            LedgerAccount.PLATFORM_FEE_REVENUE,
            LedgerDirection.CREDIT,
            platform_fee,
            role="platform_fee",
        ),
        _line(LedgerAccount.RIDER_PAYABLE, LedgerDirection.CREDIT, delivery, role="delivery_fee"),
        _line(
            LedgerAccount.PLATFORM_COMMISSION,
            LedgerDirection.CREDIT,
            commission,
            role="commission",
            commission_bps=commission_bps,
        ),
        _line(
            LedgerAccount.MERCHANT_PAYABLE,
            LedgerDirection.CREDIT,
            merchant,
            role="merchant_net",
        ),
    ):
        if draft is not None:
            lines.append(draft)

    return LedgerPostingRequest(
        event_type=LedgerEventType.ORDER_PAYMENT_CAPTURED,
        reference_key=reference_key,
        order_id=order_id,
        currency=currency,
        lines=lines,
        metadata={
            "payment_id": payment_id,
            "payment_provider": payment_provider,
            "goods_paise": goods,
            "commission_paise": commission,
            "commission_gst_paise": commission_gst,
            "merchant_payable_paise": merchant,
        },
    )


def build_refund_posting(
    *,
    reference_key: str,
    order_id: uuid.UUID,
    refund_id: str,
    payment_id: str,
    amount_paise: int,
    payment_provider: str,
    currency: str = "INR",
) -> LedgerPostingRequest:
    """Simple refund: reduce merchant payable, credit cash/receivable."""
    cash_account = (
        LedgerAccount.CUSTOMER_RECEIVABLE
        if payment_provider == "cod"
        else LedgerAccount.PLATFORM_CASH
    )
    lines = [
        LedgerLineDraft(
            account=LedgerAccount.MERCHANT_PAYABLE,
            direction=LedgerDirection.DEBIT,
            amount_paise=amount_paise,
            metadata={"role": "refund_from_merchant"},
        ),
        LedgerLineDraft(
            account=cash_account,
            direction=LedgerDirection.CREDIT,
            amount_paise=amount_paise,
            metadata={"role": "refund_outflow"},
        ),
    ]
    return LedgerPostingRequest(
        event_type=LedgerEventType.PAYMENT_REFUND,
        reference_key=reference_key,
        order_id=order_id,
        currency=currency,
        lines=lines,
        metadata={
            "refund_id": refund_id,
            "payment_id": payment_id,
            "payment_provider": payment_provider,
        },
    )
