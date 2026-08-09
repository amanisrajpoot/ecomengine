"""Settlement ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Settlement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "settlements"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    party_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    party_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING", index=True)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_paise: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="INR")
    report: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)


class SettlementLedgerLink(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "settlement_ledger_links"
    __table_args__ = (
        UniqueConstraint("ledger_entry_id", name="uq_settlement_ledger_entry"),
    )

    settlement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("settlements.id"), nullable=False, index=True
    )
    ledger_entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ledger_entries.id"), nullable=False, index=True
    )
