"""Profile Screen."""
from __future__ import annotations
from typing import Any
from app.ussd.engine.state_machine import ScreenHandler, ScreenResponse, ScreenResult
from app.ussd.engine.redis_session_store import USSDSession
from app.ussd.engine.response_builder import ResponseBuilder

class ProfileScreen(ScreenHandler):
    screen_id = "profile"
    async def handle(self, session: USSDSession, user_input: str, db: Any) -> ScreenResponse:
        builder = ResponseBuilder(provider=session.provider, language=session.language)
        return ScreenResponse(result=ScreenResult.TRANSITION, next_screen="dashboard", message="")
    async def render(self, session: USSDSession, db: Any) -> str:
        builder = ResponseBuilder(provider=session.provider, language=session.language)
        from app.models.user import User
        user = db.query(User).filter(User.phone_number == session.phone_number).first()
        return builder.end_response(f"Profile: {user.full_name if user else 'Unknown'}\n{session.phone_number}")
