"""ONDC session persistence — links Beckn transaction_id to internal cart/order."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class OndcSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ondc_sessions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "transaction_id", name="uq_ondc_session_txn"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    transaction_id: Mapped[str] = mapped_column(String(128), nullable=False)
    bap_id: Mapped[str] = mapped_column(String(256), nullable=False)
    bap_uri: Mapped[str] = mapped_column(Text, nullable=False)
    bpp_id: Mapped[str] = mapped_column(String(256), nullable=False)
    stage: Mapped[str] = mapped_column(String(32), nullable=False, default="SEARCH")
    business_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    location_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    cart_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    selected_items: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    customer_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    context_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    callback_log: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
