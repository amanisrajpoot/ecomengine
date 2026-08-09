"""Pricing pipeline — always returns a full PriceBreakdown."""

from __future__ import annotations

from typing import Any

from app.pricing.schemas import PriceBreakdown, PriceLine, PricingContext, PricingInputItem
from app.taxation.engine import calculate_customer_transaction_tax


def price_items(
    items: list[PricingInputItem],
    context: PricingContext | None = None,
    *,
    tax_rules: list[Any] | None = None,
) -> PriceBreakdown:
    """
    Pipeline:
      items → base+modifiers → discounts → delivery → platform → other fees → tax → total
    """
    ctx = context or PricingContext()
    lines: list[PriceLine] = []
    subtotal = 0
    for item in items:
        line_subtotal = (item.unit_price_paise + item.modifiers_paise) * item.quantity
        subtotal += line_subtotal
        lines.append(
            PriceLine(
                variant_id=item.variant_id,
                bundle_id=item.bundle_id,
                name=item.name,
                quantity=item.quantity,
                unit_price_paise=item.unit_price_paise,
                modifiers_paise=item.modifiers_paise,
                line_subtotal_paise=line_subtotal,
                addons=item.addons,
            )
        )

    discount = min(ctx.discount_paise, subtotal)
    taxable_base = (
        subtotal
        - discount
        + ctx.delivery_fee_paise
        + ctx.platform_fee_paise
        + ctx.other_fees_paise
    )
    tax_result = calculate_customer_transaction_tax(
        taxable_paise=max(taxable_base, 0),
        rate_bps=ctx.tax_rate_bps,
        jurisdiction=ctx.tax_jurisdiction,
        rules=tax_rules,
    )

    breakdown = PriceBreakdown(
        currency=ctx.currency,
        subtotal_paise=subtotal,
        discount_paise=discount,
        delivery_fee_paise=ctx.delivery_fee_paise,
        platform_fee_paise=ctx.platform_fee_paise,
        other_fees_paise=ctx.other_fees_paise,
        tax_paise=tax_result.tax_paise,
        tax_lines=tax_result.lines,
        total_paise=taxable_base + tax_result.tax_paise,
        lines=lines,
    )
    breakdown.assert_invariant()
    return breakdown
