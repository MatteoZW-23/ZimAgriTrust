from app.db.domain_migration_helpers import (
    create_domain_tables,
    drop_domain_tables,
)

revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None

TABLES = ['admin_approvals', 'pin_history', 'pin_lockout', 'pin_attempt', 'token_blacklist', 'rate_limits', 'security_threats', 'security_audit_logs', 'password_history', 'breached_credentials', 'fraud_alerts', 'governance_policies', 'user_consent_records', 'privacy_requests', 'disputes']

def upgrade() -> None:
    create_domain_tables(TABLES)

def downgrade() -> None:
    drop_domain_tables(TABLES)

