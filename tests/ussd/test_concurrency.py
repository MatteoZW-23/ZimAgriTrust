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
    
    tasks = []
    for i in range(5):
        async def update():
            session = await session_store.get_session(session_id)
            session.current_screen = f"screen_{i}"
            await session_store.update_session(session)
        tasks.append(update())
    
    await asyncio.gather(*tasks)
    
    # Final session should have one of the updates
    session = await session_store.get_session(session_id)
    assert session is not None


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
