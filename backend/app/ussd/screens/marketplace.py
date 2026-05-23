"""
Marketplace Screen
===================
Browse available listings.
"""
from __future__ import annotations

import logging
from typing import Any

from app.ussd.engine.state_machine import ScreenHandler, ScreenResponse, ScreenResult
from app.ussd.engine.redis_session_store import USSDSession
from app.ussd.engine.response_builder import ResponseBuilder
from sqlalchemy import desc

logger = logging.getLogger("ussd.screen.marketplace")


class MarketplaceScreen(ScreenHandler):
    """Browse marketplace listings."""

    screen_id = "marketplace"

    async def handle(self, session: USSDSession, user_input: str, db: Any) -> ScreenResponse:
        """Handle listing selection."""
        builder = ResponseBuilder(provider=session.provider, language=session.language)
        
        if user_input == "0":
            return ScreenResponse(result=ScreenResult.TRANSITION, next_screen="dashboard", message="")
        
        listing_ids = session.flow_state.get("listing_ids", [])
        try:
            idx = int(user_input) - 1
            if 0 <= idx < len(listing_ids):
                session.flow_state["selected_listing_id"] = listing_ids[idx]
                return ScreenResponse(
                    result=ScreenResult.TRANSITION,
                    next_screen="listing_view",
                    message="",
                )
        except ValueError:
            pass
        
        return ScreenResponse(result=ScreenResult.CONTINUE, message=builder.error("Invalid selection. Try again:"))

    async def render(self, session: USSDSession, db: Any) -> str:
        """Render marketplace listings."""
        builder = ResponseBuilder(provider=session.provider, language=session.language)
        
        from app.models.listing import Listing, ListingStatus
        
        listings = (
            db.query(Listing)
            .filter(Listing.status == ListingStatus.ACTIVE, Listing.quantity > 0)
            .order_by(desc(Listing.created_at))
            .limit(5)
            .all()
        )
        
        if not listings:
            return builder.end_response("No listings available now. Check back later.")
        
        lines = ["CON Available Products:"]
        listing_ids = []
        for i, l in enumerate(listings, 1):
            lines.append(f"{i}. {l.product_type} {l.quantity:.0f}kg @${l.price_per_unit:.2f}/kg")
            listing_ids.append(str(l.id))
        lines.append("0. Back")
        
        session.flow_state["listing_ids"] = listing_ids
        return "\n".join(lines)
