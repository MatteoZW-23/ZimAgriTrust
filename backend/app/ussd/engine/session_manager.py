"""
USSD Session Manager
====================
Orchestrates the full lifecycle of a USSD request:
1. Acquire distributed lock
2. Check idempotency
3. Retrieve or create session
4. Route through state machine
5. Persist updated session
6. Release lock
7. Return response

Handles: retries, duplicates, timeouts, concurrent access.
"""
from __future__ import annotations

import time
import uuid
import logging
from typing import Optional, Any

from app.ussd.engine.redis_session_store import (
    RedisSessionStore,
    USSDSession,
    session_store,
)
from app.ussd.engine.state_machine import (
    StateMachine,
    ScreenResponse,
    ScreenResult,
    state_machine,
)
from app.ussd.engine.response_builder import build_response

logger = logging.getLogger("ussd.session_manager")


class SessionManager:
    """
    Core USSD session orchestrator.
    Ensures every request is processed exactly once with distributed safety.
    """

    def __init__(
        self,
        store: RedisSessionStore = None,
        machine: StateMachine = None,
    ):
        self.store = store or session_store
        self.machine = machine or state_machine

    async def process_request(
        self,
        session_id: str,
        phone_number: str,
        user_input: str,
        provider: str,
        db: Any,
        correlation_id: str = "",
        service_code: str = "*123#",
    ) -> dict:
        """
        Process a single USSD request end-to-end.
        Returns dict with 'message' and 'end_session' keys.
        """
        if not correlation_id:
            correlation_id = uuid.uuid4().hex[:16]

        start_time = time.time()
        log_ctx = {
            "session_id": session_id,
            "phone": phone_number,
            "provider": provider,
            "correlation_id": correlation_id,
            "input": user_input[:20] if user_input else "",
        }

        # 1. Check idempotency (duplicate telco callback protection)
        idempotency_key = f"{session_id}:{len(user_input)}:{hash(user_input)}"
        cached_response = await self.store.check_idempotency(idempotency_key)
        if cached_response:
            logger.info("Idempotent replay", extra=log_ctx)
            return {"message": cached_response, "end_session": "END" in cached_response[:4]}

        # 2. Acquire distributed lock
        lock_acquired = await self.store.acquire_lock(session_id)
        if not lock_acquired:
            logger.warning("Lock contention — retrying", extra=log_ctx)
            # Wait briefly and retry once
            import asyncio
            await asyncio.sleep(0.1)
            lock_acquired = await self.store.acquire_lock(session_id)
            if not lock_acquired:
                logger.error("Lock acquisition failed", extra=log_ctx)
                return {
                    "message": "END System busy. Please try again.",
                    "end_session": True,
                }

        try:
            # 3. Retrieve or create session
            session = await self.store.get_session(session_id)
            is_new = session is None

            if is_new:
                session = await self.store.create_session(
                    session_id=session_id,
                    phone_number=phone_number,
                    provider=provider,
                    correlation_id=correlation_id,
                )
                logger.info("New session created", extra=log_ctx)
            else:
                session.retry_count += 1 if session.last_activity == session.last_activity else 0

            # Track input history
            if user_input:
                session.input_history.append(user_input)

            # 4. Route through state machine
            if is_new or not user_input:
                # Initial request — render welcome screen
                handler = self.machine.get_screen(session.current_screen)
                if handler:
                    content = await handler.render(session, db)
                    response = ScreenResponse(
                        result=ScreenResult.CONTINUE,
                        message=content,
                    )
                else:
                    response = ScreenResponse(
                        result=ScreenResult.END,
                        message="END Service unavailable.",
                        end_session=True,
                    )
            else:
                # Process user input through state machine
                response = await self.machine.process_input(session, user_input, db)

            # 5. Determine if session ends
            end_session = response.result == ScreenResult.END or response.end_session

            # 6. Format response message
            message = response.message
            if not message.startswith("CON") and not message.startswith("END"):
                if end_session:
                    message = f"END {message}"
                else:
                    message = f"CON {message}"

            # 7. Persist or destroy session
            if end_session:
                await self.store.destroy_session(session_id)
            else:
                # Update screen from response
                if response.next_screen:
                    session.current_screen = response.next_screen
                if response.flow_state_updates:
                    session.flow_state.update(response.flow_state_updates)
                await self.store.update_session(session)

            # 8. Store idempotent response
            await self.store.set_idempotency(idempotency_key, message)

            # Log performance
            elapsed = time.time() - start_time
            logger.info(
                "Request processed",
                extra={
                    **log_ctx,
                    "elapsed_ms": int(elapsed * 1000),
                    "screen": session.current_screen if not end_session else "ended",
                    "end_session": end_session,
                },
            )

            if elapsed > 3.0:
                logger.warning(
                    "USSD response exceeded 3s SLA",
                    extra={**log_ctx, "elapsed_ms": int(elapsed * 1000)},
                )

            return {"message": message, "end_session": end_session}

        except Exception as e:
            logger.error(
                "Session processing error",
                extra={**log_ctx, "error": str(e)},
                exc_info=True,
            )
            return {
                "message": "END System error. Dial *123# to start again.",
                "end_session": True,
            }

        finally:
            # 9. Always release lock
            await self.store.release_lock(session_id)

    async def recover_session(self, phone_number: str, provider: str) -> Optional[USSDSession]:
        """Attempt to recover an abandoned session for the phone number."""
        session = await self.store.get_session_by_phone(phone_number)
        if session and not session.is_expired:
            logger.info(
                "Session recovered",
                extra={"phone": phone_number, "session_id": session.session_id},
            )
            return session
        return None

    async def force_end_session(self, session_id: str) -> None:
        """Force-end a session (admin/support operation)."""
        await self.store.destroy_session(session_id)
        logger.info("Session force-ended", extra={"session_id": session_id})

    async def get_session_info(self, session_id: str) -> Optional[dict]:
        """Get session state for debugging/monitoring."""
        session = await self.store.get_session(session_id)
        if not session:
            return None
        return session.to_dict()


# Module-level singleton
session_manager = SessionManager()
