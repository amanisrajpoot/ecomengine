"""phase12_delivery

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-09 06:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "delivery_partner_profiles",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("is_online", sa.Boolean(), nullable=False),
        sa.Column("documents", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("current_lat", sa.Float(), nullable=True),
        sa.Column("current_lng", sa.Float(), nullable=True),
        sa.Column("service_area", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("display_name", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_delivery_partner_user"),
    )
    op.create_index(
        op.f("ix_delivery_partner_profiles_tenant_id"),
        "delivery_partner_profiles",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_delivery_partner_profiles_user_id"),
        "delivery_partner_profiles",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "vehicles",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("partner_id", sa.UUID(), nullable=False),
        sa.Column("vehicle_type", sa.String(length=32), nullable=False),
        sa.Column("registration", sa.String(length=64), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["partner_id"], ["delivery_partner_profiles.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_vehicles_partner_id"), "vehicles", ["partner_id"], unique=False)
    op.create_index(op.f("ix_vehicles_tenant_id"), "vehicles", ["tenant_id"], unique=False)

    op.create_table(
        "deliveries",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("fulfillment_id", sa.UUID(), nullable=False),
        sa.Column("partner_id", sa.UUID(), nullable=True),
        sa.Column("vehicle_id", sa.UUID(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("eta", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["fulfillment_id"], ["fulfillments.id"]),
        sa.ForeignKeyConstraint(["partner_id"], ["delivery_partner_profiles.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fulfillment_id", name="uq_deliveries_fulfillment_id"),
    )
    op.create_index(
        op.f("ix_deliveries_fulfillment_id"), "deliveries", ["fulfillment_id"], unique=False
    )
    op.create_index(op.f("ix_deliveries_partner_id"), "deliveries", ["partner_id"], unique=False)
    op.create_index(op.f("ix_deliveries_status"), "deliveries", ["status"], unique=False)
    op.create_index(op.f("ix_deliveries_tenant_id"), "deliveries", ["tenant_id"], unique=False)

    op.create_table(
        "delivery_stops",
        sa.Column("delivery_id", sa.UUID(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("stop_type", sa.String(length=16), nullable=False),
        sa.Column("address", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lng", sa.Float(), nullable=True),
        sa.Column("contact", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("proof", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["delivery_id"], ["deliveries.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_delivery_stops_delivery_id"), "delivery_stops", ["delivery_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_delivery_stops_delivery_id"), table_name="delivery_stops")
    op.drop_table("delivery_stops")
    op.drop_index(op.f("ix_deliveries_tenant_id"), table_name="deliveries")
    op.drop_index(op.f("ix_deliveries_status"), table_name="deliveries")
    op.drop_index(op.f("ix_deliveries_partner_id"), table_name="deliveries")
    op.drop_index(op.f("ix_deliveries_fulfillment_id"), table_name="deliveries")
    op.drop_table("deliveries")
    op.drop_index(op.f("ix_vehicles_tenant_id"), table_name="vehicles")
    op.drop_index(op.f("ix_vehicles_partner_id"), table_name="vehicles")
    op.drop_table("vehicles")
    op.drop_index(op.f("ix_delivery_partner_profiles_user_id"), table_name="delivery_partner_profiles")
    op.drop_index(
        op.f("ix_delivery_partner_profiles_tenant_id"), table_name="delivery_partner_profiles"
    )
    op.drop_table("delivery_partner_profiles")
