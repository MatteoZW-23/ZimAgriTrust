"""
USSD Session Tests
==================
Tests Redis session store, TTL, and session lifecycle.
"""
from __future__ import annotations

import asyncio
import pytest
from app.ussd.engine.redis_session_store import session_store, USSDSession


@pytest.mark.asyncio
async def test_create_session():
    """Test creating a new session."""
    session = await session_store.create_session(
        session_id="test_create_123",
        phone_number="+263712345678",
        provider="econet",
    )
    assert session.session_id == "test_create_123"
    assert session.phone_number == "+263712345678"
    assert session.current_screen == "welcome"


@pytest.mark.asyncio
async def test_get_session():
    """Test retrieving a session."""
    await session_store.create_session(
        session_id="test_get_123",
        phone_number="+263712345678",
        provider="econet",
    )
    session = await session_store.get_session("test_get_123")
    assert session is not None
    assert session.session_id == "test_get_123"


@pytest.mark.asyncio
async def test_update_session():
    """Test updating session with optimistic concurrency."""
    session = await session_store.create_session(
        session_id="test_update_123",
        phone_number="+263712345678",
        provider="econet",
    )
    version = session.version
    session.current_screen = "dashboard"
    success = await session_store.update_session(session, expected_version=version)
    assert success is True


@pytest.mark.asyncio
async def test_destroy_session():
    """Test destroying a session."""
    await session_store.create_session(
        session_id="test_destroy_123",
        phone_number="+263712345678",
        provider="econet",
    )
    await session_store.destroy_session("test_destroy_123")
    session = await session_store.get_session("test_destroy_123")
    assert session is None


@pytest.mark.asyncio
async def test_session_ttl():
    """Test session TTL expiration."""
    await session_store.create_session(
        session_id="test_ttl_123",
        phone_number="+263712345678",
        provider="econet",
        ttl=1,  # 1 second
    )
    await asyncio.sleep(2)
    session = await session_store.get_session("test_ttl_123")
    assert session is None


@pytest.mark.asyncio
async def test_distributed_lock():
    """Test distributed lock acquisition."""
    session_id = "test_lock_123"
    lock_1 = await session_store.acquire_lock(session_id)
    lock_2 = await session_store.acquire_lock(session_id)
    assert lock_1 is True
    assert lock_2 is False
    await session_store.release_lock(session_id)
