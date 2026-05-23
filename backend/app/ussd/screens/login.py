"""
Login Screen
============
PIN-based authentication for registered users.
"""
from __future__ import annotations

import logging
from typing import Any

from app.ussd.engine.state_machine import ScreenHandler, ScreenResponse, ScreenResult
from app.ussd.engine.redis_session_store import USSDSession
from app.ussd.engine.response_builder import ResponseBuilder
from app.ussd.engine.validators import validator

logger = logging.getLogger("ussd.screen.login")


class LoginScreen(ScreenHandler):
    """PIN authentication screen."""

    screen_id = "login"

    async def handle(self, session: USSDSession, user_input: str, db: Any) -> ScreenResponse:
        """Handle PIN input."""
        builder = ResponseBuilder(provider=session.provider, language=session.language)
        
        from app.models.user import User
        from app.core.security import verify_password
        
        user = db.query(User).filter(User.phone_number == session.phone_number).first()
        
        if not user or not user.ussd_pin_hash:
            return ScreenResponse(
                result=ScreenResult.END,
                message=builder.error("No PIN set. Register via the app first."),
                end_session=True,
            )
        
        valid, error = validator.validate_pin(user_input)
        if not valid:
            return ScreenResponse(result=ScreenResult.CONTINUE, message=builder.input_prompt(f"CON {error}\nEnter PIN:"))
        
        if not verify_password(user_input, user.ussd_pin_hash):
            session.pin_attempts = session.pin_attempts + 1
            if session.pin_attempts >= 3:
                return ScreenResponse(
                    result=ScreenResult.END,
                    message=builder.error("Too many wrong PINs. Account locked for 15 min."),
                    end_session=True,
                )
            return ScreenResponse(
                result=ScreenResult.CONTINUE,
                message=builder.input_prompt(f"CON Wrong PIN ({session.pin_attempts}/3). Try again:"),
            )
        
        session.user_id = str(user.id)
        session.authenticated = True
        session.pin_verified = True
        session.pin_attempts = 0
        
        post_auth_screen = session.flow_state.get("post_auth_screen", "dashboard")
        return ScreenResponse(
            result=ScreenResult.TRANSITION,
            message="",
            next_screen=post_auth_screen,
        )

    async def render(self, session: USSDSession, db: Any) -> str:
        """Render login prompt."""
        builder = ResponseBuilder(provider=session.provider, language=session.language)
        return builder.input_prompt("CON Enter your 4-digit PIN:")
