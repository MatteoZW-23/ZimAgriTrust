from app.db.domain_migration_helpers import (
    create_metadata_foreign_keys,
    drop_metadata_foreign_keys,
)

revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None

def upgrade() -> None:
    create_metadata_foreign_keys()

def downgrade() -> None:
    drop_metadata_foreign_keys()

