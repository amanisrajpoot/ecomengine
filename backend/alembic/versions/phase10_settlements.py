"""Phase 10: settlements and ledger links."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "phase10_settlements"
down_revision: Union[str, None] = "phase9_ledger"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "settlements",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("party_type", sa.String(length=32), nullable=False),
        sa.Column("party_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_paise", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("report", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_settlements_tenant_party",
        "settlements",
        ["tenant_id", "party_type", "party_id"],
        unique=False,
    )
    op.create_index(
        "ix_settlements_tenant_status",
        "settlements",
        ["tenant_id", "status"],
        unique=False,
    )
    op.create_index("ix_settlements_tenant_id", "settlements", ["tenant_id"], unique=False)

    op.create_table(
        "settlement_ledger_links",
        sa.Column("settlement_id", sa.UUID(), nullable=False),
        sa.Column("ledger_entry_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["ledger_entry_id"], ["ledger_entries.id"]),
        sa.ForeignKeyConstraint(["settlement_id"], ["settlements.id"]),
        sa.PrimaryKeyConstraint("settlement_id", "ledger_entry_id"),
        sa.UniqueConstraint("ledger_entry_id", name="uq_settlement_ledger_links_entry"),
    )
    op.create_index(
        "ix_settlement_ledger_links_settlement",
        "settlement_ledger_links",
        ["settlement_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_settlement_ledger_links_settlement", table_name="settlement_ledger_links")
    op.drop_table("settlement_ledger_links")
    op.drop_index("ix_settlements_tenant_id", table_name="settlements")
    op.drop_index("ix_settlements_tenant_status", table_name="settlements")
    op.drop_index("ix_settlements_tenant_party", table_name="settlements")
    op.drop_table("settlements")
