from app.db.domain_migration_helpers import (
    create_domain_tables,
    drop_domain_tables,
)

revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None

TABLES = ['drivers', 'driver_jobs', 'transport_requests', 'transport_quotes', 'transport_negotiations', 'negotiation_messages', 'driver_assignments', 'deliveries', 'delivery_tracking', 'order_deliveries', 'logistics_trips', 'aggregation_bookings', 'delivery_reports', 'transport_surveys', 'transport_disputes', 'transport_dispute_evidence']

def upgrade() -> None:
    create_domain_tables(TABLES)

def downgrade() -> None:
    drop_domain_tables(TABLES)

