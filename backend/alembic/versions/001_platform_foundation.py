from alembic import op

from app.db.domain_migration_helpers import (
    create_domain_tables,
    drop_domain_tables,
)

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

TABLES = ['users', 'admin_users', 'super_admins', 'user_sessions', 'mfa_configurations', 'mfa_attempt', 'roles', 'permissions', 'role_permissions', 'invitations', 'audit_logs', 'system_audits', 'admin_action_logs', 'audit_checksums', 'trust_score_events', 'farmer_profiles', 'buyer_profiles', 'agent_profiles', 'system_configs', 'support_tickets']

def upgrade() -> None:
    try:
        op.execute('CREATE EXTENSION IF NOT EXISTS pgcrypto')
    except Exception:
        # Extension might already exist, which is fine
        pass
    create_domain_tables(TABLES)

def downgrade() -> None:
    drop_domain_tables(TABLES)

