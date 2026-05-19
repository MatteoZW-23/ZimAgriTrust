"""
One-shot migration script: fix all missing tables/columns.
Run inside Docker:  docker compose exec backend python _migrate_broadcast.py
"""
from sqlalchemy import create_engine, text
import os

url = os.environ.get("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@postgres:5432/agri_trust")
engine = create_engine(url)


def table_exists(conn, name):
    r = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :t)"), {"t": name})
    return r.scalar()


def column_exists(conn, table, column):
    r = conn.execute(text(
        "SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = :t AND column_name = :c)"
    ), {"t": table, "c": column})
    return r.scalar()


with engine.connect() as conn:
    # ── 1. Create admin_users table ──
    if table_exists(conn, "admin_users"):
        print("[admin_users] already exists — skipping.")
    else:
        conn.execute(text("""
            CREATE TABLE admin_users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) NOT NULL UNIQUE,
                username VARCHAR(50) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(100) NOT NULL,
                phone VARCHAR(32),
                role VARCHAR(50) DEFAULT 'support_admin',
                role_level INTEGER DEFAULT 70,
                region VARCHAR(100),
                branch_id INTEGER,
                mfa_enabled BOOLEAN DEFAULT FALSE,
                mfa_secret VARCHAR(255),
                mfa_backup_codes JSON,
                hardware_mfa_enabled BOOLEAN DEFAULT FALSE,
                hardware_mfa_credential_id VARCHAR(255),
                hardware_mfa_public_key VARCHAR(1024),
                is_active BOOLEAN DEFAULT TRUE,
                last_login TIMESTAMPTZ,
                last_password_change TIMESTAMPTZ,
                created_by INTEGER REFERENCES admin_users(id),
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
        """))
        conn.execute(text("CREATE INDEX idx_admin_users_email ON admin_users(email);"))
        conn.execute(text("CREATE INDEX idx_admin_users_username ON admin_users(username);"))
        conn.commit()
        print("[admin_users] created.")

    # ── 2. Fix audit_logs: drop old schema, recreate with correct schema ──
    if table_exists(conn, "audit_logs"):
        if column_exists(conn, "audit_logs", "admin_id"):
            print("[audit_logs] already has correct schema — skipping.")
        else:
            print("[audit_logs] schema mismatch — dropping and recreating...")
            conn.execute(text("DROP TABLE audit_logs CASCADE;"))
            conn.commit()
            conn.execute(text("""
                CREATE TABLE audit_logs (
                    id SERIAL PRIMARY KEY,
                    admin_id INTEGER REFERENCES admin_users(id),
                    user_id UUID REFERENCES users(id),
                    action VARCHAR(100) NOT NULL,
                    entity_type VARCHAR(50),
                    entity_id VARCHAR(100),
                    old_values JSON,
                    new_values JSON,
                    details JSON,
                    ip_address VARCHAR(45),
                    user_agent VARCHAR(255),
                    request_id VARCHAR(100),
                    status VARCHAR(20) DEFAULT 'success',
                    error_message TEXT,
                    checksum VARCHAR(64) NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
            """))
            conn.execute(text("CREATE INDEX idx_audit_admin_id ON audit_logs(admin_id);"))
            conn.execute(text("CREATE INDEX idx_audit_user_id ON audit_logs(user_id);"))
            conn.execute(text("CREATE INDEX idx_audit_action ON audit_logs(action);"))
            conn.execute(text("CREATE INDEX idx_audit_entity ON audit_logs(entity_type, entity_id);"))
            conn.execute(text("CREATE INDEX idx_audit_request_id ON audit_logs(request_id);"))
            conn.execute(text("CREATE INDEX idx_audit_checksum ON audit_logs(checksum);"))
            conn.execute(text("CREATE INDEX idx_audit_created_at ON audit_logs(created_at);"))
            conn.commit()
            print("[audit_logs] recreated with correct schema.")
    else:
        conn.execute(text("""
            CREATE TABLE audit_logs (
                id SERIAL PRIMARY KEY,
                admin_id INTEGER REFERENCES admin_users(id),
                user_id UUID REFERENCES users(id),
                action VARCHAR(100) NOT NULL,
                entity_type VARCHAR(50),
                entity_id VARCHAR(100),
                old_values JSON,
                new_values JSON,
                details JSON,
                ip_address VARCHAR(45),
                user_agent VARCHAR(255),
                request_id VARCHAR(100),
                status VARCHAR(20) DEFAULT 'success',
                error_message TEXT,
                checksum VARCHAR(64) NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
        """))
        conn.execute(text("CREATE INDEX idx_audit_admin_id ON audit_logs(admin_id);"))
        conn.execute(text("CREATE INDEX idx_audit_user_id ON audit_logs(user_id);"))
        conn.execute(text("CREATE INDEX idx_audit_action ON audit_logs(action);"))
        conn.execute(text("CREATE INDEX idx_audit_entity ON audit_logs(entity_type, entity_id);"))
        conn.execute(text("CREATE INDEX idx_audit_request_id ON audit_logs(request_id);"))
        conn.execute(text("CREATE INDEX idx_audit_checksum ON audit_logs(checksum);"))
        conn.execute(text("CREATE INDEX idx_audit_created_at ON audit_logs(created_at);"))
        conn.commit()
        print("[audit_logs] created with correct schema.")

    # ── 3. Create broadcast_messages table ──
    if table_exists(conn, "broadcast_messages"):
        print("[broadcast_messages] already exists — skipping.")
    else:
        conn.execute(text("""
            DO $$ BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'broadcastaudience') THEN
                    CREATE TYPE broadcastaudience AS ENUM ('all','farmers','buyers','agents','drivers','regional');
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'broadcaststatus') THEN
                    CREATE TYPE broadcaststatus AS ENUM ('pending','scheduled','sending','sent','failed','cancelled');
                END IF;
            END $$;
        """))
        conn.execute(text("""
            CREATE TABLE broadcast_messages (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                subject VARCHAR(200),
                message TEXT NOT NULL,
                audience broadcastaudience DEFAULT 'all',
                audience_filter JSON,
                channels JSON,
                status broadcaststatus DEFAULT 'pending',
                scheduled_for TIMESTAMPTZ,
                sent_at TIMESTAMPTZ,
                sent_count INTEGER NOT NULL DEFAULT 0,
                delivered_count INTEGER NOT NULL DEFAULT 0,
                failed_count INTEGER NOT NULL DEFAULT 0,
                created_by INTEGER NOT NULL REFERENCES admin_users(id),
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
        """))
        conn.commit()
        print("[broadcast_messages] created.")

    print("\nAll migrations complete.")
