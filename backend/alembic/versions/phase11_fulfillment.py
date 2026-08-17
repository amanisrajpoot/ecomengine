"""Phase 11: fulfillments decoupled from orders."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "phase11_fulfillment"
down_revision: Union[str, None] = "phase10_settlements"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fulfillments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id", name="uq_fulfillments_order_id"),
    )
    op.create_index("ix_fulfillments_tenant_id", "fulfillments", ["tenant_id"], unique=False)
    op.create_index("ix_fulfillments_order_id", "fulfillments", ["order_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_fulfillments_order_id", table_name="fulfillments")
    op.drop_index("ix_fulfillments_tenant_id", table_name="fulfillments")
    op.drop_table("fulfillments")
