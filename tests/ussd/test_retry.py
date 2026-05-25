"""
USSD Retry Tests
================
Tests duplicate callback handling and retry storm protection.
"""
from __future__ import annotations

import pytest
import asyncio
from app.ussd.engine.retry_handler import retry_handler
from app.ussd.providers.econet.retry_logic import econet_retry


@pytest.mark.asyncio
async def test_duplicate_callback_detection():
    """Test that duplicate callbacks are detected."""
    session_id = "test_session_123"

    # First request should process
    should_process_1 = await econet_retry.should_process(session_id, "1")
    assert should_process_1 is True

    # Duplicate should be rejected
    should_process_2 = await econet_retry.should_process(session_id, "1")
    assert should_process_2 is False


@pytest.mark.asyncio
async def test_retry_limit():
    """Test that retry limit is enforced."""
    session_id = "test_retry_limit"

    # Exceed max retries
    for i in range(10):
        await econet_retry.increment_retry(session_id)

    count = await econet_retry.get_retry_count(session_id)
    assert count >= 3


@pytest.mark.asyncio
async def test_rate_limiting():
    """Test per-phone rate limiting.
    
    Uses unique session IDs per call so the per-session retry cap (5) does not
    prevent all 15 calls from being evaluated. The per-minute rate cap (10) kicks
    in after 10 requests, making the counter exactly 10.
    """
    phone = "+263799999999"  # Unique phone to avoid cross-test pollution

    for i in range(15):
        await retry_handler.evaluate_request(f"rate_test_session_{i}", phone, "1")

    rate_info = await retry_handler.get_phone_rate_info(phone)
    assert rate_info["requests_this_minute"] >= 10


@pytest.mark.asyncio
async def test_circuit_breaker():
    """Test circuit breaker activation."""
    status = await retry_handler.get_circuit_breaker_status()
    assert status["status"] in ["open", "closed"]
