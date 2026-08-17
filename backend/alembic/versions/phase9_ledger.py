"""Phase 9: immutable ledger entries."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "phase9_ledger"
down_revision: Union[str, None] = "phase8_payments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ledger_entries",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("order_id", sa.UUID(), nullable=True),
        sa.Column("event_group_id", sa.UUID(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("account", sa.String(length=64), nullable=False),
        sa.Column("direction", sa.String(length=8), nullable=False),
        sa.Column("amount_paise", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ledger_entries_tenant_order",
        "ledger_entries",
        ["tenant_id", "order_id"],
        unique=False,
    )
    op.create_index(
        "ix_ledger_entries_tenant_account",
        "ledger_entries",
        ["tenant_id", "account"],
        unique=False,
    )
    op.create_index(
        "ix_ledger_entries_event_group",
        "ledger_entries",
        ["event_group_id"],
        unique=False,
    )
    op.create_index("ix_ledger_entries_tenant_id", "ledger_entries", ["tenant_id"], unique=False)
    op.create_index("ix_ledger_entries_order_id", "ledger_entries", ["order_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_ledger_entries_order_id", table_name="ledger_entries")
    op.drop_index("ix_ledger_entries_tenant_id", table_name="ledger_entries")
    op.drop_index("ix_ledger_entries_event_group", table_name="ledger_entries")
    op.drop_index("ix_ledger_entries_tenant_account", table_name="ledger_entries")
    op.drop_index("ix_ledger_entries_tenant_order", table_name="ledger_entries")
    op.drop_table("ledger_entries")
