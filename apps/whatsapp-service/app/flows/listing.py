"""Listing flow handler for WhatsApp service."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from app.state_manager import StateManager
from app.whatsapp_bridge import WhatsAppBridgeClient

logger = logging.getLogger(__name__)


class ListingFlowHandler:
    """Handles the listing creation flow via WhatsApp."""

    def __init__(
        self,
        state_manager: StateManager,
        bridge: WhatsAppBridgeClient,
    ):
        self._state_manager = state_manager
        self._bridge = bridge

    async def handle(
        self,
        phone: str,
        body: str,
        has_media: bool = False,
        media: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Handle listing flow message."""
        state = await self._state_manager.get_state(phone)
        flow = state.get("flow")
        data = state.get("data", {})

        if flow != "CREATING_LISTING":
            return "Not in listing creation flow."

        step = data.get("step", "CROP_NAME")

        if step == "CROP_NAME":
            return await self._handle_crop_name(phone, body)
        elif step == "MEDIA":
            return await self._handle_media(phone, has_media, media, data)
        elif step == "LOCATION":
            return await self._handle_location(phone, body, data)
        elif step == "QUANTITY":
            return await self._handle_quantity(phone, body, data)
        elif step == "PRICE":
            return await self._handle_price(phone, body, data)
        elif step == "CONFIRM":
            return await self._handle_confirm(phone, body, data)
        else:
            await self._state_manager.set_idle(phone)
            return "Invalid state. Starting over."

    async def _handle_crop_name(self, phone: str, body: str) -> str:
        """Handle crop name input."""
        crop_name = body.strip().lower()

        # Validate crop (simplified - in production, query backend API)
        supported_crops = ["maize", "wheat", "soybeans", "tomatoes", "mangoes", "potatoes"]

        matched_crop = None
        for crop in supported_crops:
            if crop in crop_name or crop_name in crop:
                matched_crop = crop
                break

        if not matched_crop:
            crop_list = ", ".join([c.title() for c in supported_crops])
            return (
                f"⚠️ We currently support: {crop_list}.\n\n"
                f"Please reply with the exact crop name (e.g., 'Maize', 'Mango')"
            )

        await self._state_manager.set_state(
            phone,
            "CREATING_LISTING",
            {
                "step": "MEDIA",
                "claimed_crop": matched_crop,
                "crop_display": matched_crop.title(),
            },
        )

        return (
            f"🌱 *Listing: {matched_crop.title()}*\n\n"
            f"Please send a **clear photo** of your {matched_crop.title()}.\n\n"
            f"📸 Tips:\n"
            f"• Use good lighting\n"
            f"• Show the crop clearly\n"
            f"• Avoid blurry images\n\n"
            f"Type 'skip' to skip photo verification."
        )

    async def _handle_media(
        self,
        phone: str,
        has_media: bool,
        media: Optional[Dict[str, Any]],
        data: Dict[str, Any],
    ) -> str:
        """Handle media upload."""
        if body.strip().lower() == "skip":
            # Skip photo verification
            await self._state_manager.set_state(
                phone,
                "CREATING_LISTING",
                {
                    "step": "LOCATION",
                    "claimed_crop": data.get("claimed_crop"),
                    "crop_display": data.get("crop_display"),
                    "grade": "Standard",
                    "confidence": 0,
                },
            )
            return "Photo verification skipped.\n\n📍 What is your location (province)?"

        if not has_media:
            return "📸 Please send a photo of your crop or type 'skip' to continue without verification."

        # In production, process image with vision service
        # For now, accept any image
        claimed_crop = data.get("claimed_crop")

        await self._state_manager.set_state(
            phone,
            "CREATING_LISTING",
            {
                "step": "LOCATION",
                "claimed_crop": claimed_crop,
                "crop_display": claimed_crop.title(),
                "grade": "Standard",
                "confidence": 80,
            },
        )

        return (
            f"✅ Photo received for {claimed_crop.title()}.\n\n"
            f"📍 What is your location (province)?"
        )

    async def _handle_location(self, phone: str, body: str, data: Dict[str, Any]) -> str:
        """Handle location input."""
        location = body.strip()

        if not location:
            return "Please provide your location (province)."

        await self._state_manager.update_state_data(
            phone,
            {"step": "QUANTITY", "location": location},
        )

        return (
            f"📍 Location: {location}\n\n"
            f"📦 How much do you have? (e.g., '5 tons', '100 kg')"
        )

    async def _handle_quantity(self, phone: str, body: str, data: Dict[str, Any]) -> str:
        """Handle quantity input."""
        quantity = body.strip()

        if not quantity:
            return "Please provide the quantity (e.g., '5 tons', '100 kg')."

        await self._state_manager.update_state_data(
            phone,
            {"step": "PRICE", "quantity": quantity},
        )

        crop_display = data.get("crop_display", "crop")

        return (
            f"📦 Quantity: {quantity}\n\n"
            f"💰 What is your price per unit for {crop_display}? (e.g., '$450 per ton')"
        )

    async def _handle_price(self, phone: str, body: str, data: Dict[str, Any]) -> str:
        """Handle price input."""
        price = body.strip()

        if not price:
            return "Please provide your price (e.g., '$450 per ton')."

        await self._state_manager.update_state_data(
            phone,
            {"step": "CONFIRM", "price": price},
        )

        # Build confirmation message
        crop_display = data.get("crop_display", "crop")
        location = data.get("location", "Unknown")
        quantity = data.get("quantity", "Unknown")
        grade = data.get("grade", "Standard")

        return (
            f"📋 *Confirm Your Listing*\n\n"
            f"🌱 Crop: {crop_display}\n"
            f"📍 Location: {location}\n"
            f"📦 Quantity: {quantity}\n"
            f"💰 Price: {price}\n"
            f"⭐ Grade: {grade}\n\n"
            f"Reply 'yes' to confirm or 'no' to cancel."
        )

    async def _handle_confirm(self, phone: str, body: str, data: Dict[str, Any]) -> str:
        """Handle confirmation."""
        response = body.strip().lower()

        if response in ["yes", "y", "confirm", "ok"]:
            # In production, call backend API to create listing
            # For now, just clear state and return success
            await self._state_manager.set_idle(phone)

            crop_display = data.get("crop_display", "crop")

            return (
                f"✅ *Listing Created Successfully!*\n\n"
                f"Your {crop_display} listing is now live.\n\n"
                f"🔔 You'll be notified when buyers make offers.\n\n"
                f"Reply `menu` for more options."
            )
        elif response in ["no", "n", "cancel"]:
            await self._state_manager.set_idle(phone)
            return "❌ Listing cancelled.\n\nReply `menu` to start over."
        else:
            return "Please reply 'yes' to confirm or 'no' to cancel."
