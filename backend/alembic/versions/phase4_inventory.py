"""Phase 4: inventory_items and stock_movements."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "phase4_inventory"
down_revision: Union[str, None] = "phase3_catalog"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "inventory_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("business_id", sa.UUID(), nullable=False),
        sa.Column("location_id", sa.UUID(), nullable=False),
        sa.Column("variant_id", sa.UUID(), nullable=False),
        sa.Column("on_hand", sa.Integer(), nullable=False),
        sa.Column("reserved", sa.Integer(), nullable=False),
        sa.Column("low_stock_threshold", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()), nullable=False),
        sa.CheckConstraint("on_hand >= 0", name="ck_inventory_on_hand_nonneg"),
        sa.CheckConstraint("reserved >= 0", name="ck_inventory_reserved_nonneg"),
        sa.CheckConstraint("on_hand >= reserved", name="ck_inventory_on_hand_gte_reserved"),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"]),
        sa.ForeignKeyConstraint(["location_id"], ["business_locations.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["variant_id"], ["variants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("location_id", "variant_id", name="uq_inventory_location_variant"),
    )
    op.create_index("ix_inventory_business_location", "inventory_items", ["business_id", "location_id"], unique=False)
    op.create_index("ix_inventory_items_business_id", "inventory_items", ["business_id"], unique=False)
    op.create_index("ix_inventory_items_location_id", "inventory_items", ["location_id"], unique=False)
    op.create_index("ix_inventory_items_tenant_id", "inventory_items", ["tenant_id"], unique=False)
    op.create_index("ix_inventory_items_variant_id", "inventory_items", ["variant_id"], unique=False)

    op.create_table(
        "stock_movements",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("inventory_item_id", sa.UUID(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("delta_on_hand", sa.Integer(), nullable=False),
        sa.Column("delta_reserved", sa.Integer(), nullable=False),
        sa.Column("reference_type", sa.String(length=64), nullable=True),
        sa.Column("reference_id", sa.UUID(), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()), nullable=False),
        sa.ForeignKeyConstraint(["inventory_item_id"], ["inventory_items.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_stock_movements_item_created",
        "stock_movements",
        ["inventory_item_id", "created_at"],
        unique=False,
    )
    op.create_index("ix_stock_movements_inventory_item_id", "stock_movements", ["inventory_item_id"], unique=False)
    op.create_index("ix_stock_movements_tenant_id", "stock_movements", ["tenant_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_stock_movements_tenant_id", table_name="stock_movements")
    op.drop_index("ix_stock_movements_inventory_item_id", table_name="stock_movements")
    op.drop_index("ix_stock_movements_item_created", table_name="stock_movements")
    op.drop_table("stock_movements")
    op.drop_index("ix_inventory_items_variant_id", table_name="inventory_items")
    op.drop_index("ix_inventory_items_tenant_id", table_name="inventory_items")
    op.drop_index("ix_inventory_items_location_id", table_name="inventory_items")
    op.drop_index("ix_inventory_items_business_id", table_name="inventory_items")
    op.drop_index("ix_inventory_business_location", table_name="inventory_items")
    op.drop_table("inventory_items")
