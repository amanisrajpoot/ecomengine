"""Business locations ORM models."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Boolean, Double, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class BusinessLocation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "business_locations"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    address: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    lat: Mapped[float] = mapped_column(Double, nullable=False)
    lng: Mapped[float] = mapped_column(Double, nullable=False)
    service_area: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    hours: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    timezone: Mapped[str] = mapped_column(Text, nullable=False, default="Asia/Kolkata")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
