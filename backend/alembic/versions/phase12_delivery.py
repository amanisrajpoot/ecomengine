"""Phase 12: delivery partners, vehicles, deliveries, stops."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "phase12_delivery"
down_revision: Union[str, None] = "phase11_fulfillment"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "delivery_partner_profiles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("is_online", sa.Boolean(), nullable=False),
        sa.Column("documents", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("current_lat", sa.Double(), nullable=True),
        sa.Column("current_lng", sa.Double(), nullable=True),
        sa.Column("service_area", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_delivery_partner_profiles_user_id"),
    )
    op.create_index(
        "ix_delivery_partner_profiles_tenant_id",
        "delivery_partner_profiles",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_delivery_partner_profiles_user_id",
        "delivery_partner_profiles",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "vehicles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("partner_id", sa.UUID(), nullable=False),
        sa.Column("vehicle_type", sa.String(length=32), nullable=False),
        sa.Column("registration", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["partner_id"], ["delivery_partner_profiles.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_vehicles_tenant_id", "vehicles", ["tenant_id"], unique=False)
    op.create_index("ix_vehicles_partner_id", "vehicles", ["partner_id"], unique=False)

    op.create_table(
        "deliveries",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("fulfillment_id", sa.UUID(), nullable=False),
        sa.Column("partner_id", sa.UUID(), nullable=True),
        sa.Column("vehicle_id", sa.UUID(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("eta", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["fulfillment_id"], ["fulfillments.id"]),
        sa.ForeignKeyConstraint(["partner_id"], ["delivery_partner_profiles.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fulfillment_id", name="uq_deliveries_fulfillment_id"),
    )
    op.create_index("ix_deliveries_tenant_id", "deliveries", ["tenant_id"], unique=False)
    op.create_index("ix_deliveries_fulfillment_id", "deliveries", ["fulfillment_id"], unique=False)

    op.create_table(
        "delivery_stops",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("delivery_id", sa.UUID(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("stop_type", sa.String(length=16), nullable=False),
        sa.Column("address", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("lat", sa.Double(), nullable=False),
        sa.Column("lng", sa.Double(), nullable=False),
        sa.Column("contact", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("proof", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["delivery_id"], ["deliveries.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_delivery_stops_delivery_id", "delivery_stops", ["delivery_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_delivery_stops_delivery_id", table_name="delivery_stops")
    op.drop_table("delivery_stops")
    op.drop_index("ix_deliveries_fulfillment_id", table_name="deliveries")
    op.drop_index("ix_deliveries_tenant_id", table_name="deliveries")
    op.drop_table("deliveries")
    op.drop_index("ix_vehicles_partner_id", table_name="vehicles")
    op.drop_index("ix_vehicles_tenant_id", table_name="vehicles")
    op.drop_table("vehicles")
    op.drop_index("ix_delivery_partner_profiles_user_id", table_name="delivery_partner_profiles")
    op.drop_index("ix_delivery_partner_profiles_tenant_id", table_name="delivery_partner_profiles")
    op.drop_table("delivery_partner_profiles")
