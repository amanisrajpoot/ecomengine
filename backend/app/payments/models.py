"""Payment ORM models."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import BigInteger, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Payment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_payments_tenant_idempotency"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)  # cashfree | cod | ...
    provider_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="CREATED")
    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="INR")
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    raw: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    checkout_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)


class Refund(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "refunds"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    payment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payments.id"), nullable=False, index=True
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True
    )
    provider_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="CREATED")
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
