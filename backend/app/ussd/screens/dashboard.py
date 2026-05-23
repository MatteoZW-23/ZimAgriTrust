"""
Dashboard Screen
================
Main menu after authentication.
"""
from __future__ import annotations

import logging
from typing import Any

from app.ussd.engine.state_machine import ScreenHandler, ScreenResponse, ScreenResult
from app.ussd.engine.redis_session_store import USSDSession
from app.ussd.engine.response_builder import ResponseBuilder

logger = logging.getLogger("ussd.screen.dashboard")


class DashboardScreen(ScreenHandler):
    """Main dashboard menu."""

    screen_id = "dashboard"

    async def handle(self, session: USSDSession, user_input: str, db: Any) -> ScreenResponse:
        """Handle menu selection."""
        builder = ResponseBuilder(provider=session.provider, language=session.language)
        
        menu_map = {
            "1": "marketplace",
            "2": "wallet",
            "3": "profile",
            "4": "listing_create",
            "5": "offers",
            "6": "notifications",
            "7": "support",
            "8": "pin_change",
        }
        
        if user_input in menu_map:
            return ScreenResponse(
                result=ScreenResult.TRANSITION,
                message="",
                next_screen=menu_map[user_input],
            )
        
        return ScreenResponse(
            result=ScreenResult.CONTINUE,
            message=builder.error("Invalid option. Try again:"),
        )

    async def render(self, session: USSDSession, db: Any) -> str:
        """Render dashboard menu."""
        builder = ResponseBuilder(provider=session.provider, language=session.language)
        
        from app.models.user import User
        user = db.query(User).filter(User.phone_number == session.phone_number).first()
        name = user.full_name.split()[0] if user else "User"
        
        return builder.menu(
            title=f"CON 👋 {name}\n━━━━━━━━━━━━━━━━━━━━",
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
            footer="0. Logout",
        )
