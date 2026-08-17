"""Tax rule ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TaxRule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tax_rules"
    __table_args__ = (
        Index("ix_tax_rules_tenant_category", "tenant_id", "category"),
        Index("ix_tax_rules_effective", "effective_from", "effective_to"),
    )

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, index=True
    )
    code: Mapped[str] = mapped_column(String(16), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String(16), nullable=False, default="IN")
    rate_bps: Mapped[int] = mapped_column(Integer, nullable=False)
    inclusive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payer: Mapped[str] = mapped_column(String(32), nullable=False, default="CUSTOMER")
    kind: Mapped[str] = mapped_column(String(32), nullable=False, default="CUSTOMER_TRANSACTION")
    effective_from: Mapped[datetime] = mapped_column(nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(nullable=True)
