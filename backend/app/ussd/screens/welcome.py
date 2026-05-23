"""
Welcome Screen
==============
First screen shown when user dials *123#.
Detects if user is registered and routes accordingly.
"""
from __future__ import annotations

import logging
from typing import Any

from app.ussd.engine.state_machine import ScreenHandler, ScreenResponse, ScreenResult
from app.ussd.engine.redis_session_store import USSDSession
from app.ussd.engine.response_builder import ResponseBuilder

logger = logging.getLogger("ussd.screen.welcome")


class WelcomeScreen(ScreenHandler):
    """Welcome screen — entry point for USSD."""

    screen_id = "welcome"

    async def handle(self, session: USSDSession, user_input: str, db: Any) -> ScreenResponse:
        """Handle welcome screen input."""
        # Welcome screen is auto-rendered, no user input expected
        return ScreenResponse(
            result=ScreenResult.TRANSITION,
            message="",
            next_screen="dashboard",
        )

    async def render(self, session: USSDSession, db: Any) -> str:
        """Render welcome screen content."""
        builder = ResponseBuilder(provider=session.provider, language=session.language)
        
        # Check if user exists
        from app.models.user import User
        user = db.query(User).filter(User.phone_number == session.phone_number).first()
        
        if user:
            # Registered user
            if user.ussd_pin_hash:
                return builder.menu(
                    title="CON 🇿🇼 ZimAgritrust Marketplace\n━━━━━━━━━━━━━━━━━━━━",
                    options=[
                        ("1", "Marketplace"),
                        ("2", "My Wallet"),
                        ("3", "My Profile"),
                        ("4", "Sell Product"),
                        ("5", "My Orders"),
                        ("6", "Notifications"),
                        ("7", "Support"),
                        ("8", "Change PIN"),
                    ],
                    footer="0. Exit",
                )
            else:
                # Registered but no PIN
                return builder.input_prompt(
                    "CON Welcome back!\nYou need a PIN to access USSD.\nEnter your app password to set a 4-digit PIN:"
                )
        else:
            # New user
            return builder.menu(
                title="CON 🇿🇼 ZimAgritrust Marketplace\n━━━━━━━━━━━━━━━━━━━━",
                options=[
                    ("1", "Register"),
                    ("2", "Login with App"),
                ],
                footer="0. Exit",
            )
