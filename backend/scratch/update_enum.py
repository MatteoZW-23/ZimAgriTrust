import os
from sqlalchemy import create_engine, text
from app.core.config import settings

def update_enum():
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        print("Adding 'deleted' to listingstatus enum...")
        try:
            # Postgres doesn't allow ALTER TYPE ... ADD VALUE inside a transaction block in some versions/contexts
            # but we can try it here. SQLAlchemy's connect() might be in a transaction.
            conn.execute(text("ALTER TYPE listingstatus ADD VALUE 'deleted';"))
            conn.commit()
            print("Success!")
        except Exception as e:
            if "already exists" in str(e):
                print("Value 'deleted' already exists in enum.")
            else:
                print(f"Error updating enum: {e}")

if __name__ == "__main__":
    update_enum()
