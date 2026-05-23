"""
Registration Screen
====================
New user registration via USSD.
Collects minimal info: name, province, PIN.
"""
from __future__ import annotations

import logging
from typing import Any

from app.ussd.engine.state_machine import ScreenHandler, ScreenResponse, ScreenResult
from app.ussd.engine.redis_session_store import USSDSession
from app.ussd.engine.response_builder import ResponseBuilder
from app.ussd.engine.validators import validator

logger = logging.getLogger("ussd.screen.register")


class RegisterScreen(ScreenHandler):
    """USSD registration flow."""

    screen_id = "register"

    async def handle(self, session: USSDSession, user_input: str, db: Any) -> ScreenResponse:
        """Handle registration input."""
        builder = ResponseBuilder(provider=session.provider, language=session.language)
        step = session.flow_state.get("reg_step", "name")

        if step == "name":
            valid, error = validator.validate_text_input(user_input, min_len=2, max_len=50)
            if not valid:
                return ScreenResponse(result=ScreenResult.CONTINUE, message=builder.input_prompt(f"CON {error}\nEnter your full name:"))
            session.flow_state["reg_name"] = user_input
            session.flow_state["reg_step"] = "province"
            return ScreenResponse(
                result=ScreenResult.CONTINUE,
                message=builder.input_prompt("CON Enter your province (e.g. Harare, Bulawayo):"),
                flow_state_updates={"reg_step": "province"},
            )

        elif step == "province":
            valid, error = validator.validate_text_input(user_input, min_len=2, max_len=30)
            if not valid:
                return ScreenResponse(result=ScreenResult.CONTINUE, message=builder.input_prompt(f"CON {error}\nEnter province:"))
            session.flow_state["reg_province"] = user_input
            session.flow_state["reg_step"] = "pin"
            return ScreenResponse(
                result=ScreenResult.CONTINUE,
                message=builder.input_prompt("CON Create your 4-digit PIN:"),
                flow_state_updates={"reg_step": "pin"},
            )

        elif step == "pin":
            valid, error = validator.validate_pin(user_input)
            if not valid:
                return ScreenResponse(result=ScreenResult.CONTINUE, message=builder.input_prompt(f"CON {error}\nEnter PIN:"))
            session.flow_state["reg_pin"] = user_input
            session.flow_state["reg_step"] = "pin_confirm"
            return ScreenResponse(
                result=ScreenResult.CONTINUE,
                message=builder.input_prompt("CON Confirm your PIN:"),
                flow_state_updates={"reg_step": "pin_confirm"},
            )

        elif step == "pin_confirm":
            if user_input != session.flow_state.get("reg_pin"):
                return ScreenResponse(
                    result=ScreenResult.END,
                    message=builder.error("PINs do not match. Dial *123# to start again."),
                    end_session=True,
                )

            # Create user account
            from app.models.user import User, UserRole
            from app.core.security import get_password_hash
            import uuid

            user = User(
                id=uuid.uuid4(),
                phone_number=session.phone_number,
                full_name=session.flow_state["reg_name"],
                password_hash=get_password_hash(session.flow_state["reg_pin"]),  # Initial password = PIN
                ussd_pin_hash=get_password_hash(session.flow_state["reg_pin"]),
                role=UserRole.FARMER,
                province=session.flow_state["reg_province"],
                is_phone_verified=True,
                phone_verified_at=session.last_activity,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            session.user_id = str(user.id)
            session.authenticated = True
            session.pin_verified = True

            logger.info("USSD registration completed", extra={"phone": session.phone_number, "user_id": str(user.id)})

            return ScreenResponse(
                result=ScreenResult.END,
                message=builder.success(
                    "✅ Registration Complete!",
                    [
                        f"Welcome, {user.full_name}!",
                        "Your account is ready.",
                        "Dial *123# to access the marketplace.",
                    ],
                ),
                end_session=True,
            )

        return ScreenResponse(
            result=ScreenResult.ERROR,
            message=builder.error("Registration error. Please try again."),
            end_session=True,
        )

    async def render(self, session: USSDSession, db: Any) -> str:
        """Render registration screen."""
        builder = ResponseBuilder(provider=session.provider, language=session.language)
        step = session.flow_state.get("reg_step", "name")

        if step == "name":
            return builder.input_prompt("CON Enter your full name:")
        elif step == "province":
            return builder.input_prompt("CON Enter your province (e.g. Harare, Bulawayo):")
        elif step == "pin":
            return builder.input_prompt("CON Create your 4-digit PIN:")
        elif step == "pin_confirm":
            return builder.input_prompt("CON Confirm your PIN:")

        return builder.input_prompt("CON Enter your full name:")
