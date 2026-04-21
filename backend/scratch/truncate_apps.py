from sqlalchemy import create_engine, text
from app.core.config import settings

def truncate_apps():
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE agent_applications CASCADE;"))
        conn.commit()
        print("Table agent_applications truncated.")

if __name__ == "__main__":
    truncate_apps()
