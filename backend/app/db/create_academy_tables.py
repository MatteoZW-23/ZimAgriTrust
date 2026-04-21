from app.db.base_class import Base
from app.db.session import engine
from app.models.academy import AgentTraining, AcademyModule, ExamAttempt

def create_academy_tables():
    print("Dropping and recreated academy tables...")
    tables = [
        AgentTraining.__table__,
        AcademyModule.__table__,
        ExamAttempt.__table__
    ]
    Base.metadata.drop_all(bind=engine, tables=tables)
    Base.metadata.create_all(bind=engine, tables=tables)
    print("Tables created successfully.")


if __name__ == "__main__":
    create_academy_tables()
