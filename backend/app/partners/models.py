"""Delivery partner and vehicle ORM models."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Boolean, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DeliveryPartnerProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "delivery_partner_profiles"
    __table_args__ = (UniqueConstraint("user_id", name="uq_delivery_partner_user"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    is_online: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    documents: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    current_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    service_area: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    display_name: Mapped[str | None] = mapped_column(Text, nullable=True)


class Vehicle(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "vehicles"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("delivery_partner_profiles.id"), nullable=False, index=True
    )
    vehicle_type: Mapped[str] = mapped_column(String(32), nullable=False, default="BIKE")
    registration: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
