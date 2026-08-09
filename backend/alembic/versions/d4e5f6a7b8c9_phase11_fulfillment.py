"""phase11_fulfillment

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-08-09 06:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fulfillments",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id", name="uq_fulfillments_order_id"),
    )
    op.create_index(op.f("ix_fulfillments_order_id"), "fulfillments", ["order_id"], unique=False)
    op.create_index(op.f("ix_fulfillments_status"), "fulfillments", ["status"], unique=False)
    op.create_index(op.f("ix_fulfillments_tenant_id"), "fulfillments", ["tenant_id"], unique=False)

    op.create_table(
        "fulfillment_status_events",
        sa.Column("fulfillment_id", sa.UUID(), nullable=False),
        sa.Column("from_status", sa.String(length=64), nullable=True),
        sa.Column("to_status", sa.String(length=64), nullable=False),
        sa.Column("actor_user_id", sa.UUID(), nullable=True),
        sa.Column("actor_role", sa.String(length=64), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["fulfillment_id"], ["fulfillments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_fulfillment_status_events_fulfillment_id"),
        "fulfillment_status_events",
        ["fulfillment_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_fulfillment_status_events_fulfillment_id"),
        table_name="fulfillment_status_events",
    )
    op.drop_table("fulfillment_status_events")
    op.drop_index(op.f("ix_fulfillments_tenant_id"), table_name="fulfillments")
    op.drop_index(op.f("ix_fulfillments_status"), table_name="fulfillments")
    op.drop_index(op.f("ix_fulfillments_order_id"), table_name="fulfillments")
    op.drop_table("fulfillments")
