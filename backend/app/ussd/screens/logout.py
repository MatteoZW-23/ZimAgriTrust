"""Logout Screen."""
from __future__ import annotations
from typing import Any
from app.ussd.engine.state_machine import ScreenHandler, ScreenResponse, ScreenResult
from app.ussd.engine.redis_session_store import USSDSession
from app.ussd.engine.response_builder import ResponseBuilder

class LogoutScreen(ScreenHandler):
    screen_id = "logout"
    async def handle(self, session: USSDSession, user_input: str, db: Any) -> ScreenResponse:
        builder = ResponseBuilder(provider=session.provider, language=session.language)
        return ScreenResponse(result=ScreenResult.END, message=builder.end_response("Logged out. Dial *123# to start again."), end_session=True)
    async def render(self, session: USSDSession, db: Any) -> str:
        builder = ResponseBuilder(provider=session.provider, language=session.language)
        return builder.end_response("Logging out...")
