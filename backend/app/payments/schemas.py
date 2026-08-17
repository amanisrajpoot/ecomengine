"""Payment API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.payments.gateway import PaymentProvider


class PaymentCreate(BaseModel):
    provider: PaymentProvider = PaymentProvider.COD


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    order_id: uuid.UUID
    provider: str
    provider_ref: str | None
    status: str
    amount_paise: int
    currency: str
    idempotency_key: str | None
    raw: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class PaymentInitResponse(PaymentRead):
    client_payload: dict[str, Any] | None = None


class RefundCreate(BaseModel):
    amount_paise: int | None = Field(default=None, ge=1)
    reason: str | None = None


class RefundRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    payment_id: uuid.UUID
    order_id: uuid.UUID
    amount_paise: int
    status: str
    reason: str | None
    created_at: datetime
    updated_at: datetime
