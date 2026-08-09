"""Tax rule ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TaxRule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tax_rules"

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, index=True
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)  # CGST | SGST | IGST | CESS
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String(64), nullable=False, default="IN-INTRA")
    rate_bps: Mapped[int] = mapped_column(Integer, nullable=False)
    inclusive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payer: Mapped[str] = mapped_column(String(32), nullable=False, default="CUSTOMER")
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
