from sqlalchemy import create_engine, text
from app.core.config import settings

def check_applications():
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, full_name, national_id, status FROM agent_applications;"))
        for row in result:
            print(f"App: {row.id}, Name: {row.full_name}, ID: {row.national_id}, Status: {row.status}")

if __name__ == "__main__":
    check_applications()
