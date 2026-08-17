"""Phase 3: catalog — categories, products, variants, addons, bundles."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "phase3_catalog"
down_revision: Union[str, None] = "phase2_business_location"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("business_id", sa.UUID(), nullable=False),
        sa.Column("parent_id", sa.UUID(), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()), nullable=False),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"]),
        sa.ForeignKeyConstraint(["parent_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_categories_business_sort", "categories", ["business_id", "sort_order"], unique=False)
    op.create_index("ix_categories_business_id", "categories", ["business_id"], unique=False)
    op.create_index("ix_categories_tenant_id", "categories", ["tenant_id"], unique=False)

    op.create_table(
        "products",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("business_id", sa.UUID(), nullable=False),
        sa.Column("category_id", sa.UUID(), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("images", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()), nullable=False),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"]),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_products_business_active", "products", ["business_id", "is_active"], unique=False)
    op.create_index("ix_products_business_id", "products", ["business_id"], unique=False)
    op.create_index("ix_products_tenant_id", "products", ["tenant_id"], unique=False)

    op.create_table(
        "variants",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("sku", sa.String(length=64), nullable=True),
        sa.Column("base_price_paise", sa.BigInteger(), nullable=False),
        sa.Column("is_available", sa.Boolean(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_variants_product_available", "variants", ["product_id", "is_available"], unique=False)
    op.create_index("ix_variants_product_id", "variants", ["product_id"], unique=False)
    op.create_index("ix_variants_tenant_id", "variants", ["tenant_id"], unique=False)

    op.create_table(
        "addons",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("business_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("price_paise", sa.BigInteger(), nullable=False),
        sa.Column("max_qty", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()), nullable=False),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_addons_business_active", "addons", ["business_id", "is_active"], unique=False)
    op.create_index("ix_addons_business_id", "addons", ["business_id"], unique=False)
    op.create_index("ix_addons_tenant_id", "addons", ["tenant_id"], unique=False)

    op.create_table(
        "product_addon_links",
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("addon_id", sa.UUID(), nullable=False),
        sa.Column("group_name", sa.Text(), nullable=True),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["addon_id"], ["addons.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("product_id", "addon_id"),
    )

    op.create_table(
        "bundles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("business_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("price_paise", sa.BigInteger(), nullable=True),
        sa.Column("items", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()), nullable=False),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bundles_business_active", "bundles", ["business_id", "is_active"], unique=False)
    op.create_index("ix_bundles_business_id", "bundles", ["business_id"], unique=False)
    op.create_index("ix_bundles_tenant_id", "bundles", ["tenant_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_bundles_tenant_id", table_name="bundles")
    op.drop_index("ix_bundles_business_id", table_name="bundles")
    op.drop_index("ix_bundles_business_active", table_name="bundles")
    op.drop_table("bundles")
    op.drop_table("product_addon_links")
    op.drop_index("ix_addons_tenant_id", table_name="addons")
    op.drop_index("ix_addons_business_id", table_name="addons")
    op.drop_index("ix_addons_business_active", table_name="addons")
    op.drop_table("addons")
    op.drop_index("ix_variants_tenant_id", table_name="variants")
    op.drop_index("ix_variants_product_id", table_name="variants")
    op.drop_index("ix_variants_product_available", table_name="variants")
    op.drop_table("variants")
    op.drop_index("ix_products_tenant_id", table_name="products")
    op.drop_index("ix_products_business_id", table_name="products")
    op.drop_index("ix_products_business_active", table_name="products")
    op.drop_table("products")
    op.drop_index("ix_categories_tenant_id", table_name="categories")
    op.drop_index("ix_categories_business_id", table_name="categories")
    op.drop_index("ix_categories_business_sort", table_name="categories")
    op.drop_table("categories")
