from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("buyer_requests", sa.Column("sector", sa.String(length=50), nullable=True))
    op.alter_column("buyer_requests", "product_type", existing_type=sa.String(length=50), type_=sa.String(length=120), existing_nullable=False)


def downgrade() -> None:
    op.alter_column("buyer_requests", "product_type", existing_type=sa.String(length=120), type_=sa.String(length=50), existing_nullable=False)
    op.drop_column("buyer_requests", "sector")
