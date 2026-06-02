from app.db.domain_migration_helpers import (
    create_domain_tables,
    drop_domain_tables,
)

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None

TABLES = ['subscription_plans', 'subscriptions', 'subscription_features', 'subscription_benefits', 'billing_history', 'renewals', 'upgrades', 'downgrades', 'notification_templates', 'notification_preferences', 'notification_logs', 'broadcast_messages', 'user_communication_preferences']

def upgrade() -> None:
    create_domain_tables(TABLES)

def downgrade() -> None:
    drop_domain_tables(TABLES)

