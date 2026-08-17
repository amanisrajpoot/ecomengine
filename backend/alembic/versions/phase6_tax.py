"""Phase 6: tax_rules."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "phase6_tax"
down_revision: Union[str, None] = "phase5_cart"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tax_rules",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=True),
        sa.Column("code", sa.String(length=16), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("jurisdiction", sa.String(length=16), nullable=False),
        sa.Column("rate_bps", sa.Integer(), nullable=False),
        sa.Column("inclusive", sa.Boolean(), nullable=False),
        sa.Column("payer", sa.String(length=32), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tax_rules_tenant_category", "tax_rules", ["tenant_id", "category"], unique=False)
    op.create_index("ix_tax_rules_effective", "tax_rules", ["effective_from", "effective_to"], unique=False)
    op.create_index("ix_tax_rules_tenant_id", "tax_rules", ["tenant_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_tax_rules_tenant_id", table_name="tax_rules")
    op.drop_index("ix_tax_rules_effective", table_name="tax_rules")
    op.drop_index("ix_tax_rules_tenant_category", table_name="tax_rules")
    op.drop_table("tax_rules")
