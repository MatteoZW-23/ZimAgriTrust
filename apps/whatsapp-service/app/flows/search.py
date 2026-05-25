"""Search flow handler for WhatsApp service."""
from __future__ import annotations

import logging
from urllib.parse import urlencode

import httpx

from app.config import settings
from app.state_manager import StateManager
from app.whatsapp_bridge import WhatsAppBridgeClient

logger = logging.getLogger(__name__)


class SearchFlowHandler:
    """Handles marketplace search and listing browsing via WhatsApp."""

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
    ) -> str:
        """Handle search flow message."""
        state = await self._state_manager.get_state(phone)
        flow = state.get("flow")

        if flow != "SEARCHING":
            return "Not in search flow."

        await self._state_manager.set_idle(phone)
        search_term = body.strip()
        if not search_term:
            return "Please type the crop, input, or location you want to search for."

        query = urlencode({"kind": "all", "q": search_term, "limit": 5})
        url = f"{settings.main_backend_url.rstrip('/')}/api/v1/browse/search?{query}"

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            logger.warning("Backend listing search failed for WhatsApp flow: %s", exc)
            return "I could not reach the marketplace right now. Please try again in a moment."

        results = payload.get("results", [])
        if not results:
            return (
                f"No active listings found for *{search_term}*.\n\n"
                "Try another crop, input, or province. Reply `menu` for more options."
            )

        lines = [f"Search Results: {search_term}", ""]
        for index, item in enumerate(results[:5], start=1):
            price = float(item.get("price_per_unit") or 0)
            currency = item.get("currency") or "USD"
            quantity = float(item.get("quantity") or 0)
            unit = item.get("unit") or "unit"
            location = item.get("province") or item.get("location") or "Location not specified"
            verified = "verified" if item.get("verified") else "unverified"
            lines.extend(
                [
                    f"{index}. {item.get('name', 'Listing')} - {quantity:g} {unit} - {currency} {price:g}/{unit}",
                    f"   Location: {location} | {verified}",
                    f"   Listing ID: {item.get('id')}",
                    "",
                ]
            )

        lines.append("Reply `menu` for more options.")
        return "\n".join(lines)
