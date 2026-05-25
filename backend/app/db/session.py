import logging
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from app.core.config import settings

logger = logging.getLogger(__name__)

_PLACEHOLDER_FRAGMENTS = (
    "CHANGE_ME",
    "test-key",
    "secret-bootstrap-token",
    "your-secret",
)


def _validate_production_secrets() -> None:
    """
    Refuse to start if any critical secret is still a placeholder.
    Called once at module import time so the failure is immediate.
    """
    checks = {
        "SECRET_KEY": settings.SECRET_KEY,
        "REFRESH_SECRET_KEY": settings.REFRESH_SECRET_KEY,
    }
    violations: list[str] = []
    for name, value in checks.items():
        if any(frag in value for frag in _PLACEHOLDER_FRAGMENTS):
            violations.append(name)
    if violations:
        raise RuntimeError(
            f"FATAL — placeholder secrets detected for: {violations}. "
            "Set proper values via environment variables before starting the server."
        )


_validate_production_secrets()

engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_pre_ping=True,
    pool_size=int(getattr(settings, "DB_POOL_SIZE", 20)),
    max_overflow=int(getattr(settings, "DB_MAX_OVERFLOW", 40)),
    pool_timeout=int(getattr(settings, "DB_POOL_TIMEOUT", 30)),
    pool_recycle=int(getattr(settings, "DB_POOL_RECYCLE", 3600)),
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@event.listens_for(engine, "connect")
def _on_connect(dbapi_conn, _connection_record):
    """Set statement timeout on every new connection to prevent runaway queries."""
    if type(dbapi_conn).__name__.startswith("sqlite") or "sqlite" in str(type(dbapi_conn)).lower():
        return
    timeout_ms = int(getattr(settings, "DB_STATEMENT_TIMEOUT_MS", 30000))
    try:
        cur = dbapi_conn.cursor()
        try:
            cur.execute(f"SET statement_timeout = '{timeout_ms}ms'")
        finally:
            cur.close()
    except Exception:
        pass


def get_db():
    """Dependency for getting database session with guaranteed cleanup."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
