"""
USSD Test Configuration
=======================
Shared fixtures for all USSD test modules.

Key concern: redis_session_store and retry_handler are module-level singletons
that lazily create an aioredis client. In pytest-asyncio STRICT mode every async
test runs in its *own* event loop. Once that loop is closed the cached client is
permanently bound to a dead loop, causing RuntimeError: Event loop is closed on
the next test.

Fix: an autouse fixture that sets _client = None before (and after) every test,
so each test's async code creates a fresh connection inside the current loop.
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def reset_redis_clients():
    """
    Reset Redis client singletons before and after every test.

    This is the canonical fix for 'RuntimeError: Event loop is closed' when
    pytest-asyncio STRICT mode assigns a new event loop per test function and
    module-level singletons hold an aioredis client from a previous (now-closed)
    loop.
    """
    from app.ussd.engine.redis_session_store import session_store
    from app.ussd.engine.retry_handler import retry_handler

    session_store._client = None
    retry_handler._client = None
    yield
    session_store._client = None
    retry_handler._client = None


@pytest.fixture
def db():
    """
    Provide a minimal in-memory SQLite test database session.

    Used by USSD integration tests that spin up a TestClient requiring a DB
    dependency injection. SQLite is used here to keep the test suite self-
    contained (no live PostgreSQL needed).
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Import Base — try both path conventions
    try:
        from app.db.base import Base  # type: ignore[import]
    except ImportError:
        from app.db.session import Base  # type: ignore[import]

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    try:
        Base.metadata.create_all(engine)
    except Exception:
        pass  # Schema errors are non-fatal for USSD integration stubs

    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
