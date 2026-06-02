from app.db.domain_migration_helpers import (
    create_domain_tables,
    drop_domain_tables,
)

revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None

TABLES = []

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass

