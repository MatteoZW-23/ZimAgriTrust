from sqlalchemy import create_engine, text
from app.core.config import settings

def sync_schema():
    engine = create_engine(settings.DATABASE_URL)
    
    commands = [
        "ALTER TABLE agent_applications ADD COLUMN IF NOT EXISTS province VARCHAR(50);",
        "ALTER TABLE agent_applications ADD COLUMN IF NOT EXISTS district VARCHAR(50);",
        "ALTER TABLE agent_applications ADD COLUMN IF NOT EXISTS has_signed_contract BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE agent_applications ADD COLUMN IF NOT EXISTS id_verified BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE agent_applications ADD COLUMN IF NOT EXISTS training_modules_completed JSONB DEFAULT '[]'::jsonb;",
        "ALTER TABLE agent_applications ADD COLUMN IF NOT EXISTS equipment_issued BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE agent_applications ADD COLUMN IF NOT EXISTS shadowing_completed BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE agent_applications ADD COLUMN IF NOT EXISTS shadowing_supervisor_id UUID REFERENCES users(id);",
        "ALTER TABLE agent_applications ADD COLUMN IF NOT EXISTS shadowing_rating FLOAT;",
        "ALTER TABLE agent_applications ADD COLUMN IF NOT EXISTS has_smartphone BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE agent_applications ADD COLUMN IF NOT EXISTS has_transport BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE agent_applications ADD COLUMN IF NOT EXISTS transport_type VARCHAR(50);",
        "ALTER TABLE agent_applications ADD COLUMN IF NOT EXISTS agri_experience_years INTEGER DEFAULT 0;",
        "ALTER TABLE agent_applications ADD COLUMN IF NOT EXISTS specializations JSONB DEFAULT '[]'::jsonb;",
        "ALTER TABLE agent_applications ADD COLUMN IF NOT EXISTS supervised_tasks_count INTEGER DEFAULT 0;",
        "ALTER TABLE agent_applications ADD COLUMN IF NOT EXISTS reviewer_notes JSONB DEFAULT '[]'::jsonb;",
        "ALTER TABLE agent_applications ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP WITH TIME ZONE;",
        "DO $$ BEGIN IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='agent_applications' AND column_name='applied_at') THEN ALTER TABLE agent_applications RENAME COLUMN applied_at TO created_at; END IF; END $$;",
    ]
    
    enum_updates = [
        "ALTER TYPE applicationstatus ADD VALUE IF NOT EXISTS 'APPLIED';",
        "ALTER TYPE applicationstatus ADD VALUE IF NOT EXISTS 'DOCS_VERIFIED';",
        "ALTER TYPE applicationstatus ADD VALUE IF NOT EXISTS 'READY_FOR_SHADOWING';",
        "ALTER TYPE applicationstatus ADD VALUE IF NOT EXISTS 'READY_FOR_CERTIFICATION';",
        "ALTER TYPE applicationstatus ADD VALUE IF NOT EXISTS 'CERTIFIED';",
    ]
    
    with engine.connect() as conn:
        print("Starting manual schema synchronization for agent_applications...")
        for cmd in commands:
            try:
                conn.execute(text(cmd))
                print(f"SUCCESS: {cmd}")
            except Exception as e:
                print(f"SKIPPED/ERROR: {cmd} | {str(e)}")
        conn.commit()

    # Enum updates must happen outside transactions
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        print("Syncing ApplicationStatus enum values...")
        for cmd in enum_updates:
            try:
                conn.execute(text(cmd))
                print(f"SUCCESS: {cmd}")
            except Exception as e:
                print(f"SKIPPED/ERROR: {cmd} | {str(e)}")
    
    print("Schema sync complete.")

if __name__ == "__main__":
    sync_schema()
