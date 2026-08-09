"""Payment gateway contracts and API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CreatePaymentRequest(BaseModel):
    order_id: str
    amount_paise: int = Field(gt=0)
    currency: str = "INR"
    customer_id: str
    customer_phone: str | None = None
    customer_email: str | None = None
    return_url: str | None = None
    notify_url: str | None = None
    idempotency_key: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CreatePaymentResult(BaseModel):
    provider: str
    provider_ref: str
    status: str
    checkout: dict[str, Any] = Field(default_factory=dict)
    raw: dict[str, Any] = Field(default_factory=dict)


class VerifyPaymentRequest(BaseModel):
    provider_ref: str
    payload: dict[str, Any] = Field(default_factory=dict)


class VerifyPaymentResult(BaseModel):
    provider: str
    provider_ref: str
    status: str  # CREATED | PENDING | CAPTURED | FAILED | CANCELLED
    amount_paise: int | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class RefundPaymentRequest(BaseModel):
    provider_ref: str
    amount_paise: int = Field(gt=0)
    reason: str | None = None
    idempotency_key: str | None = None


class RefundPaymentResult(BaseModel):
    provider: str
    provider_ref: str
    status: str
    amount_paise: int
    raw: dict[str, Any] = Field(default_factory=dict)


class InitiatePaymentBody(BaseModel):
    provider: str = Field(default="cashfree", min_length=2, max_length=32)
    idempotency_key: str | None = None
    return_url: str | None = None
    notify_url: str | None = None
    customer_phone: str | None = None
    customer_email: str | None = None


class VerifyPaymentBody(BaseModel):
    provider: str | None = None
    provider_ref: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class RefundBody(BaseModel):
    amount_paise: int = Field(gt=0)
    reason: str | None = None
    idempotency_key: str | None = None


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
    checkout_payload: dict[str, Any]
    raw: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class RefundRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    payment_id: uuid.UUID
    order_id: uuid.UUID
    provider_ref: str | None
    amount_paise: int
    status: str
    reason: str | None
    raw: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class PaymentInitiateResponse(BaseModel):
    payment: PaymentRead
    order_status: str
