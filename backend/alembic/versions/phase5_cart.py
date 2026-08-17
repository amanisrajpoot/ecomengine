"""Phase 5: carts and cart_items."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "phase5_cart"
down_revision: Union[str, None] = "phase4_inventory"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "carts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("customer_id", sa.UUID(), nullable=False),
        sa.Column("business_id", sa.UUID(), nullable=True),
        sa.Column("location_id", sa.UUID(), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("pricing_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()), nullable=False),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"]),
        sa.ForeignKeyConstraint(["customer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["location_id"], ["business_locations.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_carts_tenant_customer", "carts", ["tenant_id", "customer_id"], unique=False)
    op.create_index("ix_carts_business_id", "carts", ["business_id"], unique=False)
    op.create_index("ix_carts_customer_id", "carts", ["customer_id"], unique=False)
    op.create_index("ix_carts_tenant_id", "carts", ["tenant_id"], unique=False)

    op.create_table(
        "cart_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("cart_id", sa.UUID(), nullable=False),
        sa.Column("variant_id", sa.UUID(), nullable=True),
        sa.Column("bundle_id", sa.UUID(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("addons", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("unit_price_paise", sa.BigInteger(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(["bundle_id"], ["bundles.id"]),
        sa.ForeignKeyConstraint(["cart_id"], ["carts.id"]),
        sa.ForeignKeyConstraint(["variant_id"], ["variants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cart_items_cart_id", "cart_items", ["cart_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_cart_items_cart_id", table_name="cart_items")
    op.drop_table("cart_items")
    op.drop_index("ix_carts_tenant_id", table_name="carts")
    op.drop_index("ix_carts_customer_id", table_name="carts")
    op.drop_index("ix_carts_business_id", table_name="carts")
    op.drop_index("ix_carts_tenant_customer", table_name="carts")
    op.drop_table("carts")
