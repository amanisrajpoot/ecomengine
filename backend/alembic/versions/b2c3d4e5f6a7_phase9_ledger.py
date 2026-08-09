"""phase9_ledger

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-09 05:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ledger_entries",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("order_id", sa.UUID(), nullable=True),
        sa.Column("event_group_id", sa.UUID(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("account", sa.String(length=64), nullable=False),
        sa.Column("direction", sa.String(length=8), nullable=False),
        sa.Column("amount_paise", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("reference_key", sa.String(length=128), nullable=False),
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
    )
    op.create_index(op.f("ix_ledger_entries_account"), "ledger_entries", ["account"], unique=False)
    op.create_index(
        op.f("ix_ledger_entries_event_group_id"),
        "ledger_entries",
        ["event_group_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ledger_entries_order_id"), "ledger_entries", ["order_id"], unique=False
    )
    op.create_index(
        op.f("ix_ledger_entries_reference_key"),
        "ledger_entries",
        ["reference_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ledger_entries_tenant_id"), "ledger_entries", ["tenant_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_ledger_entries_tenant_id"), table_name="ledger_entries")
    op.drop_index(op.f("ix_ledger_entries_reference_key"), table_name="ledger_entries")
    op.drop_index(op.f("ix_ledger_entries_order_id"), table_name="ledger_entries")
    op.drop_index(op.f("ix_ledger_entries_event_group_id"), table_name="ledger_entries")
    op.drop_index(op.f("ix_ledger_entries_account"), table_name="ledger_entries")
    op.drop_table("ledger_entries")
