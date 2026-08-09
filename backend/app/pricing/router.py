"""Quote endpoint for the pricing engine (no cart persistence)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import AuthContext, require_permission, resolve_tenant_id
from app.pricing.engine import price_items
from app.pricing.schemas import PriceBreakdown, PricingContext, PricingInputItem
from app.taxation.schemas import TaxKind
from app.taxation.service import load_rules_for_calculation

router = APIRouter(prefix="/pricing", tags=["pricing"])


class QuoteRequest(BaseModel):
    items: list[PricingInputItem] = Field(min_length=1)
    context: PricingContext = Field(default_factory=PricingContext)


@router.post("/quote", response_model=PriceBreakdown)
async def quote_price(
    payload: QuoteRequest,
    db: AsyncSession = Depends(get_db),
    ctx: AuthContext = Depends(require_permission("pricing.quote")),
    tenant_id: uuid.UUID | None = Depends(resolve_tenant_id),
) -> PriceBreakdown:
    _ = ctx
    rules = await load_rules_for_calculation(
        db,
        tenant_id=tenant_id,
        kind=TaxKind.CUSTOMER_TRANSACTION.value,
    )
    return price_items(payload.items, payload.context, tax_rules=rules)
