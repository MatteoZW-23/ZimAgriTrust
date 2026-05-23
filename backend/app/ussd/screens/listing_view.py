"""Listing View Screen."""
from __future__ import annotations
from typing import Any
from app.ussd.engine.state_machine import ScreenHandler, ScreenResponse, ScreenResult
from app.ussd.engine.redis_session_store import USSDSession
from app.ussd.engine.response_builder import ResponseBuilder

class ListingViewScreen(ScreenHandler):
    screen_id = "listing_view"
    async def handle(self, session: USSDSession, user_input: str, db: Any) -> ScreenResponse:
        builder = ResponseBuilder(provider=session.provider, language=session.language)
        if user_input == "0":
            return ScreenResponse(result=ScreenResult.TRANSITION, next_screen="marketplace", message="")
        if user_input == "1":
            session.flow_state["buying_listing"] = True
            return ScreenResponse(result=ScreenResult.TRANSITION, next_screen="offers", message="")
        return ScreenResponse(result=ScreenResult.CONTINUE, message=builder.error("Invalid option:"))
    async def render(self, session: USSDSession, db: Any) -> str:
        builder = ResponseBuilder(provider=session.provider, language=session.language)
        from app.models.listing import Listing
        lid = session.flow_state.get("selected_listing_id")
        listing = db.query(Listing).filter(Listing.id == lid).first()
        if not listing:
            return builder.end_response("Listing not found.")
        return builder.confirmation(
            f"{listing.product_type}",
            [f"Qty: {listing.quantity:.0f}kg", f"Price: ${listing.price_per_unit:.2f}/kg", f"Location: {listing.location_province}"],
            "1. Buy  0. Back"
        )
