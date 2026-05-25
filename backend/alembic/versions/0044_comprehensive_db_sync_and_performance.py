"""Comprehensive database synchronization and performance optimization.

This migration:
1. Creates missing tables from models that were never migrated
2. Adds missing columns to existing tables
3. Adds performance indexes on frequently queried columns
4. Fixes foreign key constraints
5. Resolves table name conflicts (ShadowingLog)

Revision ID: 0044
Revises: 0043
Create Date: 2026-05-25
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "0044"
down_revision = "0043"
branch_labels = None
depends_on = None


def _add_column_if_not_exists(conn, table: str, column: str, definition: str):
    """Helper: add a column only if it doesn't already exist."""
    result = conn.execute(text(
        f"SELECT 1 FROM information_schema.columns "
        f"WHERE table_name = '{table}' AND column_name = '{column}'"
    ))
    if not result.fetchone():
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))


def _create_index_if_not_exists(conn, index_name: str, table: str, columns: str, unique: bool = False):
    """Helper: create an index only if it doesn't already exist."""
    result = conn.execute(text(
        f"SELECT 1 FROM pg_indexes WHERE indexname = '{index_name}'"
    ))
    if not result.fetchone():
        unique_str = "UNIQUE " if unique else ""
        conn.execute(text(f"CREATE {unique_str}INDEX IF NOT EXISTS {index_name} ON {table} ({columns})"))


def upgrade() -> None:
    conn = op.get_bind()

    # ========================================================================
    # 1. CREATE MISSING TABLES
    # ========================================================================

    # Academy modules table (from academy.py)
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS academy_modules (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            module_number INTEGER NOT NULL,
            title VARCHAR(200) NOT NULL,
            description VARCHAR(500),
            content_url VARCHAR(500),
            topics JSON,
            quiz_questions JSON,
            passing_score FLOAT DEFAULT 80.0,
            duration_hours FLOAT DEFAULT 2.0,
            order_num INTEGER NOT NULL,
            is_mandatory BOOLEAN DEFAULT TRUE
        )
    """))
    _create_index_if_not_exists(conn, "ix_academy_modules_module_number", "academy_modules", "module_number")
    _create_index_if_not_exists(conn, "ix_academy_modules_order_num", "academy_modules", "order_num")

    # Academy exam attempts table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS academy_exam_attempts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
            exam_type VARCHAR(50) NOT NULL,
            score FLOAT NOT NULL,
            answers JSON,
            passed BOOLEAN DEFAULT FALSE,
            attempted_at TIMESTAMPTZ DEFAULT now()
        )
    """))
    _create_index_if_not_exists(conn, "ix_academy_exam_attempts_agent_id", "academy_exam_attempts", "agent_id")
    _create_index_if_not_exists(conn, "ix_academy_exam_attempts_exam_type", "academy_exam_attempts", "exam_type")

    # Academy practical assessments table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS academy_practical_assessments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
            test_type VARCHAR(50) NOT NULL,
            score FLOAT NOT NULL,
            passing_score FLOAT NOT NULL,
            passed BOOLEAN DEFAULT FALSE,
            answers JSON,
            evaluator_notes VARCHAR(2000),
            attempts INTEGER DEFAULT 1,
            submitted_at TIMESTAMPTZ DEFAULT now()
        )
    """))
    _create_index_if_not_exists(conn, "ix_academy_practical_assessments_agent_id", "academy_practical_assessments", "agent_id")
    _create_index_if_not_exists(conn, "ix_academy_practical_assessments_test_type", "academy_practical_assessments", "test_type")

    # Agent shadowing logs table (from academy.py - distinct from onboarding shadowing_logs)
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS agent_shadowing_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
            senior_agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
            assignment_id UUID REFERENCES agent_assignments(id) ON DELETE SET NULL,
            task_type VARCHAR(50),
            observation_notes VARCHAR(2000),
            agent_actions VARCHAR(2000),
            senior_feedback VARCHAR(2000),
            status VARCHAR(20) DEFAULT 'pending',
            approved_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT now()
        )
    """))
    _create_index_if_not_exists(conn, "ix_agent_shadowing_logs_agent_id", "agent_shadowing_logs", "agent_id")
    _create_index_if_not_exists(conn, "ix_agent_shadowing_logs_senior_agent_id", "agent_shadowing_logs", "senior_agent_id")

    # Agent supervised reviews table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS agent_supervised_reviews (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
            reviewer_agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
            assignment_id UUID REFERENCES agent_assignments(id) ON DELETE SET NULL,
            submission JSON,
            review_notes VARCHAR(2000),
            accuracy_score FLOAT,
            is_approved BOOLEAN DEFAULT FALSE,
            reviewed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT now()
        )
    """))
    _create_index_if_not_exists(conn, "ix_agent_supervised_reviews_agent_id", "agent_supervised_reviews", "agent_id")
    _create_index_if_not_exists(conn, "ix_agent_supervised_reviews_reviewer_agent_id", "agent_supervised_reviews", "reviewer_agent_id")

    # Training modules table (from onboarding.py)
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS training_modules (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            title VARCHAR(100),
            description TEXT,
            video_url VARCHAR(255),
            order_num INTEGER,
            min_pass_score FLOAT DEFAULT 80.0,
            quiz_data JSON
        )
    """))

    # Agent training progress table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS agent_training_progress (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            application_id UUID REFERENCES agent_applications(id) ON DELETE CASCADE,
            module_id UUID REFERENCES training_modules(id) ON DELETE CASCADE,
            status VARCHAR(20) DEFAULT 'not_started',
            video_progress_percent FLOAT DEFAULT 0.0,
            quiz_score FLOAT,
            attempts INTEGER DEFAULT 0,
            completed_at TIMESTAMPTZ
        )
    """))
    _create_index_if_not_exists(conn, "ix_agent_training_progress_application_id", "agent_training_progress", "application_id")
    _create_index_if_not_exists(conn, "ix_agent_training_progress_module_id", "agent_training_progress", "module_id")

    # Agent contracts table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS agent_contracts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            application_id UUID REFERENCES agent_applications(id) ON DELETE CASCADE UNIQUE,
            contract_type VARCHAR(50) DEFAULT 'service_level_agreement',
            content_hash VARCHAR(64) NOT NULL,
            signed_by_name VARCHAR(100) NOT NULL,
            ip_address VARCHAR(45),
            signed_at TIMESTAMPTZ DEFAULT now(),
            signature_base64 TEXT,
            is_active BOOLEAN DEFAULT TRUE
        )
    """))
    _create_index_if_not_exists(conn, "ix_agent_contracts_application_id", "agent_contracts", "application_id", unique=True)

    # Shadowing logs table (from onboarding.py - distinct from academy)
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS shadowing_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            application_id UUID REFERENCES agent_applications(id) ON DELETE CASCADE,
            supervisor_id UUID REFERENCES users(id) ON DELETE CASCADE,
            tasks_observed INTEGER DEFAULT 0,
            tasks_led INTEGER DEFAULT 0,
            technical_accuracy INTEGER NOT NULL,
            professionalism INTEGER NOT NULL,
            communication INTEGER NOT NULL,
            reviewer_notes TEXT,
            recommendation VARCHAR(50),
            created_at TIMESTAMPTZ DEFAULT now()
        )
    """))
    _create_index_if_not_exists(conn, "ix_shadowing_logs_application_id", "shadowing_logs", "application_id")
    _create_index_if_not_exists(conn, "ix_shadowing_logs_supervisor_id", "shadowing_logs", "supervisor_id")

    # Trust score events table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS trust_score_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            previous_score INTEGER NOT NULL,
            new_score INTEGER NOT NULL,
            delta INTEGER NOT NULL,
            reason VARCHAR(100) NOT NULL,
            details TEXT,
            triggered_by VARCHAR(50),
            created_at TIMESTAMPTZ DEFAULT now()
        )
    """))
    _create_index_if_not_exists(conn, "ix_trust_score_events_user_id", "trust_score_events", "user_id")
    _create_index_if_not_exists(conn, "ix_trust_score_events_created_at", "trust_score_events", "created_at")

    # Transport surveys table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS transport_surveys (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE UNIQUE,
            submitted_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            transport_method VARCHAR(50),
            transport_cost_usd FLOAT,
            distance_km FLOAT,
            would_use_platform_transport BOOLEAN,
            satisfaction_rating INTEGER,
            notes TEXT,
            created_at TIMESTAMPTZ DEFAULT now()
        )
    """))
    _create_index_if_not_exists(conn, "ix_transport_surveys_order_id", "transport_surveys", "order_id", unique=True)

    # ========================================================================
    # 2. ADD MISSING COLUMNS
    # ========================================================================

    # Listings table - missing columns
    listings_cols = [
        ("boosted_until", "TIMESTAMPTZ"),
        ("view_count", "INTEGER DEFAULT 0 NOT NULL"),
        ("photo_urls", "JSON"),
        ("expires_at", "TIMESTAMPTZ"),
    ]
    for col, defn in listings_cols:
        _add_column_if_not_exists(conn, "listings", col, defn)

    # Orders table - ensure all columns exist
    orders_cols = [
        ("fulfilled_by_agent_id", "UUID REFERENCES agents(id)"),
        ("field_support_by_agent_id", "UUID REFERENCES agents(id)"),
    ]
    for col, defn in orders_cols:
        _add_column_if_not_exists(conn, "orders", col, defn)

    # Agent training table - ensure all columns exist
    agent_training_cols = [
        ("last_exam_started_at", "TIMESTAMPTZ"),
        ("active_exam_question_ids", "JSON"),
    ]
    for col, defn in agent_training_cols:
        _add_column_if_not_exists(conn, "agent_training", col, defn)

    # ========================================================================
    # 3. ADD PERFORMANCE INDEXES
    # ========================================================================

    # Users table
    _create_index_if_not_exists(conn, "ix_users_email", "users", "email")
    _create_index_if_not_exists(conn, "ix_users_role", "users", "role")
    _create_index_if_not_exists(conn, "ix_users_status", "users", "status")
    _create_index_if_not_exists(conn, "ix_users_trust_score", "users", "trust_score")
    _create_index_if_not_exists(conn, "ix_users_created_at", "users", "created_at")

    # Listings table
    _create_index_if_not_exists(conn, "ix_listings_status", "listings", "status")
    _create_index_if_not_exists(conn, "ix_listings_sector", "listings", "sector")
    _create_index_if_not_exists(conn, "ix_listings_product_type", "listings", "product_type")
    _create_index_if_not_exists(conn, "ix_listings_created_at", "listings", "created_at")
    _create_index_if_not_exists(conn, "ix_listings_is_boosted", "listings", "is_boosted")
    _create_index_if_not_exists(conn, "ix_listings_verification_status", "listings", "verification_status")

    # Orders table
    _create_index_if_not_exists(conn, "ix_orders_status", "orders", "status")
    _create_index_if_not_exists(conn, "ix_orders_buyer_id", "orders", "buyer_id")
    _create_index_if_not_exists(conn, "ix_orders_seller_id", "orders", "seller_id")
    _create_index_if_not_exists(conn, "ix_orders_created_at", "orders", "created_at")
    _create_index_if_not_exists(conn, "ix_orders_payment_reference", "orders", "payment_reference")

    # Offers table
    _create_index_if_not_exists(conn, "ix_offers_status", "offers", "status")
    _create_index_if_not_exists(conn, "ix_offers_created_at", "offers", "created_at")

    # Agents table
    _create_index_if_not_exists(conn, "ix_agents_status", "agents", "status")
    _create_index_if_not_exists(conn, "ix_agents_specialization", "agents", "specialization")
    _create_index_if_not_exists(conn, "ix_agents_province", "agents", "province")
    _create_index_if_not_exists(conn, "ix_agents_district", "agents", "district")
    _create_index_if_not_exists(conn, "ix_agents_is_available", "agents", "is_available")

    # Agent assignments table
    _create_index_if_not_exists(conn, "ix_agent_assignments_listing_id", "agent_assignments", "listing_id")
    _create_index_if_not_exists(conn, "ix_agent_assignments_order_id", "agent_assignments", "order_id")
    _create_index_if_not_exists(conn, "ix_agent_assignments_dispute_id", "agent_assignments", "dispute_id")
    _create_index_if_not_exists(conn, "ix_agent_assignments_assigned_at", "agent_assignments", "assigned_at")

    # Disputes table
    _create_index_if_not_exists(conn, "ix_disputes_status", "disputes", "status")
    _create_index_if_not_exists(conn, "ix_disputes_type", "disputes", "type")
    _create_index_if_not_exists(conn, "ix_disputes_created_at", "disputes", "created_at")

    # Transactions table
    _create_index_if_not_exists(conn, "ix_transactions_type", "transactions", "type")
    _create_index_if_not_exists(conn, "ix_transactions_status", "transactions", "status")
    _create_index_if_not_exists(conn, "ix_transactions_created_at", "transactions", "created_at")

    # Supplier profiles table
    _create_index_if_not_exists(conn, "ix_supplier_profiles_verification_status", "supplier_profiles", "verification_status")
    _create_index_if_not_exists(conn, "ix_supplier_profiles_subscription_status", "supplier_profiles", "subscription_status")
    _create_index_if_not_exists(conn, "ix_supplier_profiles_business_type", "supplier_profiles", "business_type")

    # Supplier products table
    _create_index_if_not_exists(conn, "ix_supplier_products_status", "supplier_products", "status")
    _create_index_if_not_exists(conn, "ix_supplier_products_product_type", "supplier_products", "product_type")
    _create_index_if_not_exists(conn, "ix_supplier_products_is_boosted", "supplier_products", "is_boosted")
    _create_index_if_not_exists(conn, "ix_supplier_products_is_featured", "supplier_products", "is_featured")

    # Supplier orders table
    _create_index_if_not_exists(conn, "ix_supplier_orders_status", "supplier_orders", "status")
    _create_index_if_not_exists(conn, "ix_supplier_orders_payment_status", "supplier_orders", "payment_status")
    _create_index_if_not_exists(conn, "ix_supplier_orders_created_at", "supplier_orders", "created_at")

    # Drivers table
    _create_index_if_not_exists(conn, "ix_drivers_status", "drivers", "status")
    _create_index_if_not_exists(conn, "ix_drivers_current_district", "drivers", "current_district")

    # Driver jobs table
    _create_index_if_not_exists(conn, "ix_driver_jobs_status", "driver_jobs", "status")
    _create_index_if_not_exists(conn, "ix_driver_jobs_driver_id", "driver_jobs", "driver_id")
    _create_index_if_not_exists(conn, "ix_driver_jobs_created_at", "driver_jobs", "created_at")

    # Agent applications table
    _create_index_if_not_exists(conn, "ix_agent_applications_status", "agent_applications", "status")
    _create_index_if_not_exists(conn, "ix_agent_applications_province", "agent_applications", "province")
    _create_index_if_not_exists(conn, "ix_agent_applications_district", "agent_applications", "district")
    _create_index_if_not_exists(conn, "ix_agent_applications_created_at", "agent_applications", "created_at")

    # ========================================================================
    # 4. FIX FOREIGN KEY CONSTRAINTS
    # ========================================================================

    # Ensure agent_assignments has proper foreign key constraints
    conn.execute(text("""
        ALTER TABLE agent_assignments 
        DROP CONSTRAINT IF EXISTS agent_assignments_listing_id_fkey
    """))
    conn.execute(text("""
        ALTER TABLE agent_assignments 
        ADD CONSTRAINT agent_assignments_listing_id_fkey 
        FOREIGN KEY (listing_id) REFERENCES listings(id) ON DELETE SET NULL
    """))

    conn.execute(text("""
        ALTER TABLE agent_assignments 
        DROP CONSTRAINT IF EXISTS agent_assignments_order_id_fkey
    """))
    conn.execute(text("""
        ALTER TABLE agent_assignments 
        ADD CONSTRAINT agent_assignments_order_id_fkey 
        FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL
    """))

    conn.execute(text("""
        ALTER TABLE agent_assignments 
        DROP CONSTRAINT IF EXISTS agent_assignments_dispute_id_fkey
    """))
    conn.execute(text("""
        ALTER TABLE agent_assignments 
        ADD CONSTRAINT agent_assignments_dispute_id_fkey 
        FOREIGN KEY (dispute_id) REFERENCES disputes(id) ON DELETE SET NULL
    """))

    # ========================================================================
    # 5. FIX DATA TYPE ISSUES
    # ========================================================================

    # Fix academy_modules.order -> order_num (order is a reserved word)
    try:
        conn.execute(text("ALTER TABLE academy_modules RENAME COLUMN order TO order_num"))
    except Exception:
        pass  # Column might already be renamed

    # Fix training_modules.order -> order_num
    try:
        conn.execute(text("ALTER TABLE training_modules RENAME COLUMN order TO order_num"))
    except Exception:
        pass  # Column might already be renamed


def downgrade() -> None:
    conn = op.get_bind()

    # Drop tables in reverse order of creation
    tables_to_drop = [
        "trust_score_events",
        "shadowing_logs",
        "agent_contracts",
        "agent_training_progress",
        "training_modules",
        "agent_supervised_reviews",
        "agent_shadowing_logs",
        "academy_practical_assessments",
        "academy_exam_attempts",
        "academy_modules",
        "transport_surveys",
    ]

    for table in tables_to_drop:
        conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))

    # Drop added columns (optional - can skip to preserve data)
    # listings
    for col in ["boosted_until", "view_count", "photo_urls", "expires_at"]:
        try:
            conn.execute(text(f"ALTER TABLE listings DROP COLUMN IF EXISTS {col}"))
        except Exception:
            pass

    # orders
    for col in ["fulfilled_by_agent_id", "field_support_by_agent_id"]:
        try:
            conn.execute(text(f"ALTER TABLE orders DROP COLUMN IF EXISTS {col}"))
        except Exception:
            pass

    # agent_training
    for col in ["last_exam_started_at", "active_exam_question_ids"]:
        try:
            conn.execute(text(f"ALTER TABLE agent_training DROP COLUMN IF EXISTS {col}"))
        except Exception:
            pass

    # Drop indexes (PostgreSQL will drop them with tables, but explicit is safe)
    indexes_to_drop = [
        "ix_users_email", "ix_users_role", "ix_users_status", "ix_users_trust_score", "ix_users_created_at",
        "ix_listings_status", "ix_listings_sector", "ix_listings_product_type", "ix_listings_created_at",
        "ix_listings_is_boosted", "ix_listings_verification_status",
        "ix_orders_status", "ix_orders_buyer_id", "ix_orders_seller_id", "ix_orders_created_at",
        "ix_orders_payment_reference",
        "ix_offers_status", "ix_offers_created_at",
        "ix_agents_status", "ix_agents_specialization", "ix_agents_province", "ix_agents_district",
        "ix_agents_is_available",
        "ix_agent_assignments_listing_id", "ix_agent_assignments_order_id", "ix_agent_assignments_dispute_id",
        "ix_agent_assignments_assigned_at",
        "ix_disputes_status", "ix_disputes_type", "ix_disputes_created_at",
        "ix_transactions_type", "ix_transactions_status", "ix_transactions_created_at",
        "ix_supplier_profiles_verification_status", "ix_supplier_profiles_subscription_status",
        "ix_supplier_profiles_business_type",
        "ix_supplier_products_status", "ix_supplier_products_product_type", "ix_supplier_products_is_boosted",
        "ix_supplier_products_is_featured",
        "ix_supplier_orders_status", "ix_supplier_orders_payment_status", "ix_supplier_orders_created_at",
        "ix_drivers_status", "ix_drivers_current_district",
        "ix_driver_jobs_status", "ix_driver_jobs_driver_id", "ix_driver_jobs_created_at",
        "ix_agent_applications_status", "ix_agent_applications_province", "ix_agent_applications_district",
        "ix_agent_applications_created_at",
    ]

    for index in indexes_to_drop:
        try:
            conn.execute(text(f"DROP INDEX IF EXISTS {index}"))
        except Exception:
            pass
