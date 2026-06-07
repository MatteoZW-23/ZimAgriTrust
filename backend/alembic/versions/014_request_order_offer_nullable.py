from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("orders", "offer_id", existing_type=sa.UUID(), nullable=True)


def downgrade() -> None:
    op.alter_column("orders", "offer_id", existing_type=sa.UUID(), nullable=False)
