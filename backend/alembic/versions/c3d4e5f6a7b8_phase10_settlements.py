"""phase10_settlements

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-08-09 06:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "settlements",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("party_type", sa.String(length=32), nullable=False),
        sa.Column("party_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_paise", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("report", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_settlements_party_id"), "settlements", ["party_id"], unique=False)
    op.create_index(op.f("ix_settlements_party_type"), "settlements", ["party_type"], unique=False)
    op.create_index(op.f("ix_settlements_status"), "settlements", ["status"], unique=False)
    op.create_index(op.f("ix_settlements_tenant_id"), "settlements", ["tenant_id"], unique=False)

    op.create_table(
        "settlement_ledger_links",
        sa.Column("settlement_id", sa.UUID(), nullable=False),
        sa.Column("ledger_entry_id", sa.UUID(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["ledger_entry_id"], ["ledger_entries.id"]),
        sa.ForeignKeyConstraint(["settlement_id"], ["settlements.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ledger_entry_id", name="uq_settlement_ledger_entry"),
    )
    op.create_index(
        op.f("ix_settlement_ledger_links_ledger_entry_id"),
        "settlement_ledger_links",
        ["ledger_entry_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_settlement_ledger_links_settlement_id"),
        "settlement_ledger_links",
        ["settlement_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_settlement_ledger_links_settlement_id"),
        table_name="settlement_ledger_links",
    )
    op.drop_index(
        op.f("ix_settlement_ledger_links_ledger_entry_id"),
        table_name="settlement_ledger_links",
    )
    op.drop_table("settlement_ledger_links")
    op.drop_index(op.f("ix_settlements_tenant_id"), table_name="settlements")
    op.drop_index(op.f("ix_settlements_status"), table_name="settlements")
    op.drop_index(op.f("ix_settlements_party_type"), table_name="settlements")
    op.drop_index(op.f("ix_settlements_party_id"), table_name="settlements")
    op.drop_table("settlements")
