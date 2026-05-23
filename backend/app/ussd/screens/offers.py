"""Offers Screen."""
from __future__ import annotations
from typing import Any
from app.ussd.engine.state_machine import ScreenHandler, ScreenResponse, ScreenResult
from app.ussd.engine.redis_session_store import USSDSession
from app.ussd.engine.response_builder import ResponseBuilder
from app.ussd.engine.validators import validator

class OffersScreen(ScreenHandler):
    screen_id = "offers"
    async def handle(self, session: USSDSession, user_input: str, db: Any) -> ScreenResponse:
        builder = ResponseBuilder(provider=session.provider, language=session.language)
        step = session.flow_state.get("offer_step", "qty")
        if step == "qty":
            valid, qty, err = validator.validate_quantity(user_input)
            if not valid:
                return ScreenResponse(result=ScreenResult.CONTINUE, message=builder.input_prompt(f"CON {err}\nEnter qty:"))
            session.flow_state["offer_qty"] = qty
            session.flow_state["offer_step"] = "confirm"
            return ScreenResponse(result=ScreenResult.CONTINUE, message=builder.input_prompt("CON Confirm buy? 1=Yes 2=No:"))
        if step == "confirm":
            if user_input == "1":
                return ScreenResponse(result=ScreenResult.TRANSITION, next_screen="escrow", message="")
            return ScreenResponse(result=ScreenResult.TRANSITION, next_screen="dashboard", message="")
        return ScreenResponse(result=ScreenResult.CONTINUE, message=builder.input_prompt("CON Enter quantity (kg):"))
    async def render(self, session: USSDSession, db: Any) -> str:
        builder = ResponseBuilder(provider=session.provider, language=session.language)
        return builder.input_prompt("CON Enter quantity to buy (kg):")
