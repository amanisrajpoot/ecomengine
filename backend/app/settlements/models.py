"""Settlement ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Settlement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "settlements"
    __table_args__ = (
        Index("ix_settlements_tenant_party", "tenant_id", "party_type", "party_id"),
        Index("ix_settlements_tenant_status", "tenant_id", "status"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    party_type: Mapped[str] = mapped_column(String(32), nullable=False)
    party_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_paise: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="INR")
    report: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)


class SettlementLedgerLink(Base):
    __tablename__ = "settlement_ledger_links"
    __table_args__ = (
        UniqueConstraint("ledger_entry_id", name="uq_settlement_ledger_links_entry"),
        Index("ix_settlement_ledger_links_settlement", "settlement_id"),
    )

    settlement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("settlements.id"), primary_key=True
    )
    ledger_entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ledger_entries.id"), primary_key=True
    )
