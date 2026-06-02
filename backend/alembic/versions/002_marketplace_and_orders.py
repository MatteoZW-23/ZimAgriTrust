from app.db.domain_migration_helpers import (
    create_domain_tables,
    drop_domain_tables,
)

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

TABLES = ['listings', 'offers', 'trade_sessions', 'trade_messages', 'buyer_requests', 'farmer_responses', 'saved_listings', 'listing_reports', 'orders', 'payments', 'transactions', 'trade_reviews', 'price_history', 'listing_verification_reports']

def upgrade() -> None:
    create_domain_tables(TABLES)

def downgrade() -> None:
    drop_domain_tables(TABLES)

