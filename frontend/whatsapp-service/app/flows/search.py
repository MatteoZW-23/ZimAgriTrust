"""Search flow handler for WhatsApp service."""
from __future__ import annotations

import logging

from app.state_manager import StateManager
from app.whatsapp_bridge import WhatsAppBridgeClient

logger = logging.getLogger(__name__)


class SearchFlowHandler:
    """Handles the search/listing browsing flow via WhatsApp."""

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

        # In production, query backend API for listings
        # For now, return mock results
        await self._state_manager.set_idle(phone)

        search_term = body.strip()

        return (
            f"🔍 *Search Results: {search_term}*\n\n"
            f"Found 3 listings:\n\n"
            f"1. Maize - 5 tons - $450/ton\n"
            f"   Location: Mashonaland East\n"
            f"   Reply 'view 1' for details\n\n"
            f"2. Wheat - 3 tons - $520/ton\n"
            f"   Location: Mashonaland West\n"
            f"   Reply 'view 2' for details\n\n"
            f"3. Soybeans - 2 tons - $600/ton\n"
            f"   Location: Midlands\n"
            f"   Reply 'view 3' for details\n\n"
            f"Reply `menu` for more options."
        )
