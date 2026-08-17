"""Phase 2: businesses and business_locations."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "phase2_business_location"
down_revision: Union[str, None] = "phase1_foundation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "businesses",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.Text(), nullable=True),
        sa.Column("contact", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("capabilities", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_businesses_tenant_id", "businesses", ["tenant_id"], unique=False)
    op.create_index("ix_businesses_tenant_status", "businesses", ["tenant_id", "status"], unique=False)
    op.create_index("ix_businesses_tenant_type", "businesses", ["tenant_id", "type"], unique=False)

    op.create_table(
        "business_locations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("business_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("address", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("lat", sa.Double(), nullable=False),
        sa.Column("lng", sa.Double(), nullable=False),
        sa.Column("service_area", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("hours", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("timezone", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()), nullable=False),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_business_locations_tenant_id", "business_locations", ["tenant_id"], unique=False)
    op.create_index("ix_business_locations_business_id", "business_locations", ["business_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_business_locations_business_id", table_name="business_locations")
    op.drop_index("ix_business_locations_tenant_id", table_name="business_locations")
    op.drop_table("business_locations")
    op.drop_index("ix_businesses_tenant_type", table_name="businesses")
    op.drop_index("ix_businesses_tenant_status", table_name="businesses")
    op.drop_index("ix_businesses_tenant_id", table_name="businesses")
    op.drop_table("businesses")
