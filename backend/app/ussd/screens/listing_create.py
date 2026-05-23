"""
Listing Create Screen
======================
Create a new product listing.
"""
from __future__ import annotations

import logging
from typing import Any

from app.ussd.engine.state_machine import ScreenHandler, ScreenResponse, ScreenResult
from app.ussd.engine.redis_session_store import USSDSession
from app.ussd.engine.response_builder import ResponseBuilder
from app.ussd.engine.validators import validator

logger = logging.getLogger("ussd.screen.listing_create")


class ListingCreateScreen(ScreenHandler):
    """Create product listing flow."""

    screen_id = "listing_create"

    async def handle(self, session: USSDSession, user_input: str, db: Any) -> ScreenResponse:
        """Handle listing creation input."""
        builder = ResponseBuilder(provider=session.provider, language=session.language)
        step = session.flow_state.get("create_step", "product")
        
        if step == "product":
            valid, error = validator.validate_text_input(user_input, min_len=2, max_len=30)
            if not valid:
                return ScreenResponse(result=ScreenResult.CONTINUE, message=builder.input_prompt(f"CON {error}\nEnter product:"))
            session.flow_state["create_product"] = user_input
            session.flow_state["create_step"] = "quantity"
            return ScreenResponse(result=ScreenResult.CONTINUE, message=builder.input_prompt("CON Enter quantity (kg):"))
        
        elif step == "quantity":
            valid, qty, error = validator.validate_quantity(user_input)
            if not valid:
                return ScreenResponse(result=ScreenResult.CONTINUE, message=builder.input_prompt(f"CON {error}\nEnter quantity (kg):"))
            session.flow_state["create_qty"] = qty
            session.flow_state["create_step"] = "price"
            return ScreenResponse(result=ScreenResult.CONTINUE, message=builder.input_prompt("CON Enter price per kg (USD):"))
        
        elif step == "price":
            valid, price, error = validator.validate_amount(user_input)
            if not valid:
                return ScreenResponse(result=ScreenResult.CONTINUE, message=builder.input_prompt(f"CON {error}\nEnter price:"))
            session.flow_state["create_price"] = price
            session.flow_state["create_step"] = "confirm"
            total = session.flow_state["create_qty"] * price
            return ScreenResponse(
                result=ScreenResult.CONTINUE,
                message=builder.confirmation(
                    "Confirm Listing:",
                    [
                        f"Product: {session.flow_state['create_product']}",
                        f"Quantity: {session.flow_state['create_qty']:.0f}kg",
                        f"Price: ${price:.2f}/kg",
                        f"Total: ${total:.2f}",
                    ],
                ),
            )
        
        elif step == "confirm":
            if user_input != "1":
                return ScreenResponse(result=ScreenResult.TRANSITION, next_screen="dashboard", message="")
            
            from app.models.listing import Listing, ListingStatus, Sector
            from app.models.user import User
            import uuid
            
            user = db.query(User).filter(User.phone_number == session.phone_number).first()
            if not user:
                return ScreenResponse(result=ScreenResult.END, message=builder.error("User not found."), end_session=True)
            
            listing = Listing(
                seller_id=user.id,
                sector=Sector.CROPS,
                product_type=session.flow_state["create_product"],
                quantity=float(session.flow_state["create_qty"]),
                price_per_unit=float(session.flow_state["create_price"]),
                location_province=user.province or "Zimbabwe",
                status=ListingStatus.ACTIVE,
            )
            db.add(listing)
            db.commit()
            db.refresh(listing)
            
            return ScreenResponse(
                result=ScreenResult.END,
                message=builder.success(
                    "✅ Listing Created!",
                    [f"{listing.product_type} {listing.quantity:.0f}kg @${listing.price_per_unit:.2f}/kg"],
                ),
                end_session=True,
            )
        
        return ScreenResponse(result=ScreenResult.ERROR, message=builder.error("Error. Try again."), end_session=True)

    async def render(self, session: USSDSession, db: Any) -> str:
        """Render listing creation step."""
        builder = ResponseBuilder(provider=session.provider, language=session.language)
        step = session.flow_state.get("create_step", "product")
        
        if step == "product":
            return builder.input_prompt("CON Enter product name (e.g. Maize):")
        elif step == "quantity":
            return builder.input_prompt("CON Enter quantity (kg):")
        elif step == "price":
            return builder.input_prompt("CON Enter price per kg (USD):")
        
        return builder.input_prompt("CON Enter product name:")
