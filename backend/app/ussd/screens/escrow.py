"""Escrow Screen."""
from __future__ import annotations
from typing import Any
from app.ussd.engine.state_machine import ScreenHandler, ScreenResponse, ScreenResult
from app.ussd.engine.redis_session_store import USSDSession
from app.ussd.engine.response_builder import ResponseBuilder

class EscrowScreen(ScreenHandler):
    screen_id = "escrow"
    async def handle(self, session: USSDSession, user_input: str, db: Any) -> ScreenResponse:
        builder = ResponseBuilder(provider=session.provider, language=session.language)
        return ScreenResponse(result=ScreenResult.END, message=builder.success("Order placed in escrow. You'll be notified."), end_session=True)
    async def render(self, session: USSDSession, db: Any) -> str:
        builder = ResponseBuilder(provider=session.provider, language=session.language)
        return builder.end_response("Processing escrow...")
