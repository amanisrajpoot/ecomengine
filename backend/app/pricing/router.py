"""Quote endpoint for the pricing engine (no cart persistence)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.deps import AuthContext, require_permission
from app.pricing.engine import price_items
from app.pricing.schemas import PriceBreakdown, PricingContext, PricingInputItem
from pydantic import BaseModel, Field

router = APIRouter(prefix="/pricing", tags=["pricing"])


class QuoteRequest(BaseModel):
    items: list[PricingInputItem] = Field(min_length=1)
    context: PricingContext = Field(default_factory=PricingContext)


@router.post("/quote", response_model=PriceBreakdown)
async def quote_price(
    payload: QuoteRequest,
    ctx: AuthContext = Depends(require_permission("pricing.quote")),
) -> PriceBreakdown:
    _ = ctx
    return price_items(payload.items, payload.context)
