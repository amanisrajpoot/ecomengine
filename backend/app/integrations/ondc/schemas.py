"""ONDC Beckn-style request/response schemas (adapter boundary only)."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field


class OndcContext(BaseModel):
    domain: str = Field(default="ONDC:RET10", min_length=1)
    city: str = Field(default="std:080", min_length=1)
    country: str = Field(default="IND", min_length=1)
    action: str = Field(min_length=1)
    bpp_id: str | None = None
    bpp_uri: str | None = None
    transaction_id: str | None = None
    message_id: str | None = None
    timestamp: str | None = None


class OndcProvider(BaseModel):
    id: str
    name: str
    type: str
    descriptor: dict[str, Any] = Field(default_factory=dict)


class OndcItem(BaseModel):
    id: str
    provider_id: str
    product_id: str
    name: str
    price_paise: int
    currency: str = "INR"


class OndcSearchMessage(BaseModel):
    category_id: str | None = None
    business_type: str | None = None


class OndcSearchRequest(BaseModel):
    context: OndcContext
    message: OndcSearchMessage = Field(default_factory=OndcSearchMessage)


class OndcSearchResponse(BaseModel):
    context: OndcContext
    message: dict[str, Any]


class OndcSelectLine(BaseModel):
    variant_id: uuid.UUID
    quantity: int = Field(default=1, ge=1)


class OndcSelectMessage(BaseModel):
    customer_id: uuid.UUID
    business_id: uuid.UUID
    items: list[OndcSelectLine] = Field(min_length=1)


class OndcSelectRequest(BaseModel):
    context: OndcContext
    message: OndcSelectMessage


class OndcQuote(BaseModel):
    cart_id: uuid.UUID
    currency: str
    total_paise: int
    subtotal_paise: int
    tax_paise: int


class OndcSelectResponse(BaseModel):
    context: OndcContext
    message: dict[str, Any]


class OndcInitMessage(BaseModel):
    customer_id: uuid.UUID
    cart_id: uuid.UUID


class OndcInitRequest(BaseModel):
    context: OndcContext
    message: OndcInitMessage


class OndcInitResponse(BaseModel):
    context: OndcContext
    message: dict[str, Any]


class OndcConfirmMessage(BaseModel):
    customer_id: uuid.UUID
    cart_id: uuid.UUID
    fulfillment_type: str = "DELIVERY"


class OndcConfirmRequest(BaseModel):
    context: OndcContext
    message: OndcConfirmMessage


class OndcConfirmResponse(BaseModel):
    context: OndcContext
    message: dict[str, Any]


class OndcStatusMessage(BaseModel):
    order_id: uuid.UUID


class OndcStatusRequest(BaseModel):
    context: OndcContext
    message: OndcStatusMessage


class OndcStatusResponse(BaseModel):
    context: OndcContext
    message: dict[str, Any]
