import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set test environment variables before importing app
os.environ["SECRET_KEY"] = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6"
os.environ["REFRESH_SECRET_KEY"] = "r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6"
os.environ["ADMIN_BOOTSTRAP_TOKEN"] = "test-bootstrap-token-not-default-value"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["CORS_ORIGINS"] = "*"
os.environ["ALLOWED_HOSTS"] = "*"
os.environ["RATE_LIMIT_ENABLED"] = "false"

from app.db.base import Base
from app.db.session import get_db
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def db_engine():
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    def _get_test_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as test_client:
        yield test_client
