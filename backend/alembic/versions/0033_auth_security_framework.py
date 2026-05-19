"""Add new UserRole enum values for complete auth security framework

Revision ID: 0033
Revises: 0032_supplier_module
Create Date: 2026-05-18

Adds roles: driver, staff, branch_admin, support_admin, regional_admin, finance_admin, system_admin
Ensures pin_history, password_history, mfa_configurations tables exist
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = '0033'
down_revision = '0032'
branch_labels = None
depends_on = None


def upgrade():
    # Add new enum values to userrole type
    # PostgreSQL requires ALTER TYPE to add values
    new_roles = [
        'driver', 'staff', 'branch_admin', 'support_admin',
        'regional_admin', 'finance_admin', 'system_admin',
    ]
    
    for role in new_roles:
        op.execute(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_enum
                    WHERE enumlabel = '{role}'
                    AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'userrole')
                ) THEN
                    ALTER TYPE userrole ADD VALUE '{role}';
                END IF;
            END $$;
        """)

    # Ensure pin_history table exists
    op.execute("""
        CREATE TABLE IF NOT EXISTS pin_history (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            pin_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
            changed_at TIMESTAMPTZ,
            change_reason VARCHAR(50),
            changed_by UUID REFERENCES users(id)
        );
        CREATE INDEX IF NOT EXISTS ix_pin_history_user_id ON pin_history(user_id);
    """)

    # Ensure password_history table exists
    op.execute("""
        CREATE TABLE IF NOT EXISTS password_history (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_password_history_user_id ON password_history(user_id);
    """)

    # Ensure mfa_configurations table exists
    op.execute("""
        CREATE TABLE IF NOT EXISTS mfa_configurations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            totp_secret VARCHAR(255),
            totp_backup_codes JSONB,
            yubikey_public_id VARCHAR(64),
            webauthn_credential_id VARCHAR(255),
            recovery_phone VARCHAR(32),
            status VARCHAR(30) NOT NULL DEFAULT 'disabled',
            enabled_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_mfa_configurations_user_id ON mfa_configurations(user_id);
    """)

    # Ensure mfa_attempt table exists
    op.execute("""
        CREATE TABLE IF NOT EXISTS mfa_attempt (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            method VARCHAR(20) NOT NULL,
            success BOOLEAN NOT NULL DEFAULT FALSE,
            ip_address VARCHAR(45),
            attempted_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_mfa_attempt_user_id ON mfa_attempt(user_id);
    """)

    # Ensure pin_lockout table exists
    op.execute("""
        CREATE TABLE IF NOT EXISTS pin_lockout (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            failed_attempts INTEGER NOT NULL DEFAULT 0,
            locked_until TIMESTAMPTZ,
            lockout_count INTEGER DEFAULT 0,
            last_attempt_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_pin_lockout_user_id ON pin_lockout(user_id);
    """)

    # Ensure pin_attempt table exists
    op.execute("""
        CREATE TABLE IF NOT EXISTS pin_attempt (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            channel VARCHAR(20) NOT NULL,
            success BOOLEAN NOT NULL DEFAULT FALSE,
            ip_address VARCHAR(45),
            device_fingerprint VARCHAR(255),
            attempted_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_pin_attempt_user_id ON pin_attempt(user_id);
        CREATE INDEX IF NOT EXISTS ix_pin_attempt_attempted_at ON pin_attempt(attempted_at);
    """)

    # Ensure security_audit_logs table exists
    op.execute("""
        CREATE TABLE IF NOT EXISTS security_audit_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            action VARCHAR(50) NOT NULL,
            user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            actor_id UUID REFERENCES users(id) ON DELETE SET NULL,
            resource_type VARCHAR(50),
            resource_id UUID,
            ip_address VARCHAR(45),
            user_agent VARCHAR(255),
            session_id UUID,
            details JSONB,
            status VARCHAR(20) DEFAULT 'success',
            status_code INTEGER,
            created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_security_audit_logs_user_action ON security_audit_logs(user_id, action);
        CREATE INDEX IF NOT EXISTS ix_security_audit_logs_resource ON security_audit_logs(resource_type, resource_id);
        CREATE INDEX IF NOT EXISTS ix_security_audit_logs_created_at ON security_audit_logs(created_at);
    """)


def downgrade():
    # Cannot easily remove enum values in PostgreSQL
    # Tables are left in place (non-destructive)
    pass
