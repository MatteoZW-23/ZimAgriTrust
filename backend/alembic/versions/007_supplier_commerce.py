from app.db.domain_migration_helpers import (
    create_domain_tables,
    drop_domain_tables,
)

revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None

TABLES = ['supplier_profiles', 'supplier_documents', 'supplier_products', 'supplier_orders', 'supplier_order_items', 'supplier_stock_history', 'supplier_wallet_transactions', 'supplier_csv_imports', 'supplier_reviews', 'supplier_discounts', 'input_categories', 'input_listings', 'input_offers', 'input_orders', 'input_reports', 'input_price_alerts', 'input_saved_searches']

def upgrade() -> None:
    create_domain_tables(TABLES)

def downgrade() -> None:
    drop_domain_tables(TABLES)

