"""phase20_ondc_sessions

Revision ID: g7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-08-09 06:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "g7b8c9d0e1f2"
down_revision: Union[str, None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ondc_sessions",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("transaction_id", sa.String(length=128), nullable=False),
        sa.Column("bap_id", sa.String(length=256), nullable=False),
        sa.Column("bap_uri", sa.Text(), nullable=False),
        sa.Column("bpp_id", sa.String(length=256), nullable=False),
        sa.Column("stage", sa.String(length=32), nullable=False),
        sa.Column("business_id", sa.UUID(), nullable=True),
        sa.Column("location_id", sa.UUID(), nullable=True),
        sa.Column("cart_id", sa.UUID(), nullable=True),
        sa.Column("order_id", sa.UUID(), nullable=True),
        sa.Column("selected_items", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("customer_phone", sa.String(length=32), nullable=True),
        sa.Column("context_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("callback_log", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "transaction_id", name="uq_ondc_session_txn"),
    )
    op.create_index(op.f("ix_ondc_sessions_tenant_id"), "ondc_sessions", ["tenant_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_ondc_sessions_tenant_id"), table_name="ondc_sessions")
    op.drop_table("ondc_sessions")
