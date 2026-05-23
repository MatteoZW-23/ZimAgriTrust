"""Wallet Screen."""
from __future__ import annotations
from typing import Any
from app.ussd.engine.state_machine import ScreenHandler, ScreenResponse, ScreenResult
from app.ussd.engine.redis_session_store import USSDSession
from app.ussd.engine.response_builder import ResponseBuilder

class WalletScreen(ScreenHandler):
    screen_id = "wallet"
    async def handle(self, session: USSDSession, user_input: str, db: Any) -> ScreenResponse:
        builder = ResponseBuilder(provider=session.provider, language=session.language)
        if user_input == "0":
            return ScreenResponse(result=ScreenResult.TRANSITION, next_screen="dashboard", message="")
        return ScreenResponse(result=ScreenResult.CONTINUE, message=builder.error("Invalid option:"))
    async def render(self, session: USSDSession, db: Any) -> str:
        builder = ResponseBuilder(provider=session.provider, language=session.language)
        from app.models.user import User
        user = db.query(User).filter(User.phone_number == session.phone_number).first()
        balance = user.wallet_balance_usd if user else 0
        return builder.menu(
            "CON My Wallet",
            [("1", f"Balance: ${balance:.2f}"), ("2", "History")],
            "0. Back"
        )
