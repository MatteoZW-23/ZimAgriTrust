"""
USSD Concurrency Tests
======================
Tests concurrent session handling and race conditions.
"""
from __future__ import annotations

import pytest
import asyncio
from app.ussd.engine.redis_session_store import session_store


@pytest.mark.asyncio
async def test_concurrent_session_creation():
    """Test creating sessions concurrently."""
    tasks = []
    for i in range(10):
        task = session_store.create_session(
            session_id=f"concurrent_{i}",
            phone_number=f"+26371234567{i}",
            provider="econet",
        )
        tasks.append(task)

    await asyncio.gather(*tasks)

    # Verify all sessions exist
    for i in range(10):
        session = await session_store.get_session(f"concurrent_{i}")
        assert session is not None


@pytest.mark.asyncio
async def test_concurrent_updates():
    """Test concurrent session updates with optimistic concurrency."""
    session_id = "concurrent_update_123"
    await session_store.create_session(
        session_id=session_id,
        phone_number="+263712345678",
        provider="econet",
    )

    results = []

    async def update(screen_name: str):
        session = await session_store.get_session(session_id)
        if session is None:
            return
        session.current_screen = screen_name
        success = await session_store.update_session(session)
        results.append(success)

    await asyncio.gather(*[update(f"screen_{i}") for i in range(5)])

    # Final session should still exist
    session = await session_store.get_session(session_id)
    assert session is not None
    # At least one update succeeded
    assert any(results)


@pytest.mark.asyncio
async def test_session_recovery():
    """Test session recovery by phone number."""
    phone = "+263712345678"
    await session_store.create_session(
        session_id="recovery_123",
        phone_number=phone,
        provider="econet",
    )

    recovered = await session_store.get_session_by_phone(phone)
    assert recovered is not None
    assert recovered.session_id == "recovery_123"
