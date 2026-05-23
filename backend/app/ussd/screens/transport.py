"""Transport Screen."""
from __future__ import annotations
from typing import Any
from app.ussd.engine.state_machine import ScreenHandler, ScreenResponse, ScreenResult
from app.ussd.engine.redis_session_store import USSDSession
from app.ussd.engine.response_builder import ResponseBuilder

class TransportScreen(ScreenHandler):
    screen_id = "transport"
    async def handle(self, session: USSDSession, user_input: str, db: Any) -> ScreenResponse:
        builder = ResponseBuilder(provider=session.provider, language=session.language)
        return ScreenResponse(result=ScreenResult.TRANSITION, next_screen="dashboard", message="")
    async def render(self, session: USSDSession, db: Any) -> str:
        builder = ResponseBuilder(provider=session.provider, language=session.language)
        return builder.end_response("Transport options coming soon.")
