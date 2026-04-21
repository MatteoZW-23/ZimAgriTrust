from sqlalchemy import create_engine, text
from app.core.config import settings

def check_enum():
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT n.nspname as schema, t.typname as type, e.enumlabel as label FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace WHERE t.typname = 'applicationstatus' ORDER BY e.enumsortorder;"))
        for row in result:
            print(f"Enum: {row.type}, Label: {row.label}")

if __name__ == "__main__":
    check_enum()
