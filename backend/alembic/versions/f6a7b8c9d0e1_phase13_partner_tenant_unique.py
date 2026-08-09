"""phase13_partner_tenant_unique

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-08-09 06:30:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("uq_delivery_partner_user", "delivery_partner_profiles", type_="unique")
    op.create_unique_constraint(
        "uq_delivery_partner_tenant_user",
        "delivery_partner_profiles",
        ["tenant_id", "user_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_delivery_partner_tenant_user", "delivery_partner_profiles", type_="unique"
    )
    op.create_unique_constraint(
        "uq_delivery_partner_user", "delivery_partner_profiles", ["user_id"]
    )
