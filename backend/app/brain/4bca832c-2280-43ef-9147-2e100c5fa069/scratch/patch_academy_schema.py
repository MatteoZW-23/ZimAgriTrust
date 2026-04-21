import logging
import uuid
from sqlalchemy import create_engine, text, inspect
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Extract DB URL from settings and ensure it's psycopg2 compatible
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(db_url)

def patch_agent_training_schema():
    inspector = inspect(engine)
    columns = [c['name'] for c in inspector.get_columns('agent_training')]
    
    missing_columns = {
        "last_exam_started_at": "TIMESTAMP WITH TIME ZONE",
        "active_exam_question_ids": "JSON"
    }
    
    with engine.connect() as conn:
        for col_name, col_type in missing_columns.items():
            if col_name not in columns:
                logger.info(f"Adding missing column: {col_name} to agent_training table")
                try:
                    conn.execute(text(f"ALTER TABLE agent_training ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    logger.info(f"Successfully added {col_name}")
                except Exception as e:
                    logger.error(f"Failed to add {col_name}: {e}")
            else:
                logger.info(f"Column {col_name} already exists in agent_training")

if __name__ == "__main__":
    patch_agent_training_schema()
