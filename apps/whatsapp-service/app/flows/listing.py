"""Listing flow handler for WhatsApp service."""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, Optional

import httpx

from app.config import settings
from app.state_manager import StateManager
from app.whatsapp_bridge import WhatsAppBridgeClient

logger = logging.getLogger(__name__)


class ListingFlowHandler:
    """Handles listing creation via WhatsApp."""

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
        state = await self._state_manager.get_state(phone)
        if state.get("flow") != "CREATING_LISTING":
            return "Not in listing creation flow."

        data = state.get("data", {})
        step = data.get("step", "CROP_NAME")

        if step == "CROP_NAME":
            return await self._handle_crop_name(phone, body)
        if step == "MEDIA":
            return await self._handle_media(phone, body, has_media, media, data)
        if step == "LOCATION":
            return await self._handle_location(phone, body)
        if step == "QUANTITY":
            return await self._handle_quantity(phone, body, data)
        if step == "PRICE":
            return await self._handle_price(phone, body, data)
        if step == "CONFIRM":
            return await self._handle_confirm(phone, body, data)

        await self._state_manager.set_idle(phone)
        return "Invalid state. Starting over."

    async def _handle_crop_name(self, phone: str, body: str) -> str:
        crop_name = body.strip().lower()
        supported_crops = ["maize", "wheat", "soybeans", "tomatoes", "mangoes", "potatoes"]

        matched_crop = next((crop for crop in supported_crops if crop in crop_name or crop_name in crop), None)
        if not matched_crop:
            crop_list = ", ".join(c.title() for c in supported_crops)
            return f"We currently support: {crop_list}.\n\nPlease reply with the exact crop name."

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
            f"Listing: {matched_crop.title()}\n\n"
            f"Send a clear photo of your {matched_crop.title()}, or type `skip` to continue without photo verification."
        )

    async def _handle_media(
        self,
        phone: str,
        body: str,
        has_media: bool,
        media: Optional[Dict[str, Any]],
        data: Dict[str, Any],
    ) -> str:
        claimed_crop = data.get("claimed_crop")
        if body.strip().lower() == "skip":
            await self._state_manager.set_state(
                phone,
                "CREATING_LISTING",
                {
                    "step": "LOCATION",
                    "claimed_crop": claimed_crop,
                    "crop_display": data.get("crop_display"),
                    "grade": "Standard",
                    "confidence": 0,
                },
            )
            return "Photo verification skipped.\n\nWhat is your location or province?"

        if not has_media:
            return "Please send a crop photo or type `skip` to continue without photo verification."

        await self._state_manager.set_state(
            phone,
            "CREATING_LISTING",
            {
                "step": "LOCATION",
                "claimed_crop": claimed_crop,
                "crop_display": claimed_crop.title(),
                "grade": "Standard",
                "confidence": 80,
                "media": media or {},
            },
        )
        return f"Photo received for {claimed_crop.title()}.\n\nWhat is your location or province?"

    async def _handle_location(self, phone: str, body: str) -> str:
        location = body.strip()
        if not location:
            return "Please provide your location or province."

        await self._state_manager.update_state_data(phone, {"step": "QUANTITY", "location": location})
        return f"Location: {location}\n\nHow much do you have? Example: `5 tons` or `100 kg`."

    async def _handle_quantity(self, phone: str, body: str, data: Dict[str, Any]) -> str:
        quantity = body.strip()
        amount, _unit = self._parse_quantity(quantity)
        if amount <= 0:
            return "Please provide a numeric quantity. Example: `5 tons` or `100 kg`."

        await self._state_manager.update_state_data(phone, {"step": "PRICE", "quantity": quantity})
        return f"Quantity: {quantity}\n\nWhat is your price per unit for {data.get('crop_display', 'crop')}?"

    async def _handle_price(self, phone: str, body: str, data: Dict[str, Any]) -> str:
        price = body.strip()
        if self._parse_price(price) <= 0:
            return "Please provide a numeric price. Example: `$450 per ton` or `0.45 per kg`."

        await self._state_manager.update_state_data(phone, {"step": "CONFIRM", "price": price})
        return (
            "Confirm Your Listing\n\n"
            f"Crop: {data.get('crop_display', 'crop')}\n"
            f"Location: {data.get('location', 'Unknown')}\n"
            f"Quantity: {data.get('quantity', 'Unknown')}\n"
            f"Price: {price}\n"
            f"Grade: {data.get('grade', 'Standard')}\n\n"
            "Reply `yes` to confirm or `no` to cancel."
        )

    async def _handle_confirm(self, phone: str, body: str, data: Dict[str, Any]) -> str:
        response = body.strip().lower()
        if response in ["yes", "y", "confirm", "ok"]:
            quantity, quantity_unit = self._parse_quantity(data.get("quantity", ""))
            price = self._parse_price(data.get("price", ""))
            if quantity <= 0 or price <= 0:
                return "Quantity or price could not be read. Reply `no` to cancel, then create the listing again."

            crop_display = data.get("crop_display", "crop")
            try:
                listing_id = await self._create_backend_listing(
                    phone=phone,
                    crop=crop_display,
                    quantity=quantity,
                    quantity_unit=quantity_unit,
                    price_per_unit=price,
                    location=data.get("location"),
                    grade=data.get("grade", "Standard"),
                )
            except httpx.HTTPStatusError as exc:
                logger.warning("WhatsApp listing creation rejected: %s", exc.response.text)
                return "We could not create this listing. Please check that your account is active and registered as a farmer."
            except (httpx.HTTPError, RuntimeError):
                logger.exception("WhatsApp listing creation failed")
                return "We could not create this listing right now. Please try again shortly."

            await self._state_manager.set_idle(phone)
            return (
                "Listing Created Successfully\n\n"
                f"Your {crop_display} listing is now live.\n"
                f"Listing ID: {listing_id}\n\n"
                "You will be notified when buyers make offers.\n\n"
                "Reply `menu` for more options."
            )

        if response in ["no", "n", "cancel"]:
            await self._state_manager.set_idle(phone)
            return "Listing cancelled.\n\nReply `menu` to start over."

        return "Please reply `yes` to confirm or `no` to cancel."

    @staticmethod
    def _parse_quantity(value: str) -> tuple[float, str]:
        match = re.search(r"(\d+(?:\.\d+)?)\s*([a-zA-Z]+)?", value or "")
        if not match:
            return 0.0, "kg"
        amount = float(match.group(1))
        unit = (match.group(2) or "kg").lower()
        if unit in {"ton", "tons", "tonne", "tonnes", "t"}:
            return amount * 1000, "kg"
        return amount, unit

    @staticmethod
    def _parse_price(value: str) -> float:
        match = re.search(r"(\d+(?:\.\d+)?)", value or "")
        return float(match.group(1)) if match else 0.0

    async def _create_backend_listing(
        self,
        phone: str,
        crop: str,
        quantity: float,
        quantity_unit: str,
        price_per_unit: float,
        location: Optional[str],
        grade: str,
    ) -> str:
        if not settings.internal_service_token:
            raise RuntimeError("internal_service_token is not configured")

        url = f"{settings.main_backend_url.rstrip('/')}/api/v1/whatsapp/listings"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                json={
                    "phone": phone,
                    "crop": crop,
                    "quantity": quantity,
                    "quantity_unit": quantity_unit,
                    "price_per_unit": price_per_unit,
                    "currency": "USD",
                    "province": location,
                    "grade": grade,
                },
                headers={"X-Internal-Service-Token": settings.internal_service_token},
            )
            response.raise_for_status()
            return response.json()["id"]
