"""Dispute flow handler for WhatsApp service."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from app.state_manager import StateManager
from app.whatsapp_bridge import WhatsAppBridgeClient

logger = logging.getLogger(__name__)


class DisputeFlowHandler:
    """Handles the dispute creation flow via WhatsApp."""

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
        """Handle dispute flow message."""
        state = await self._state_manager.get_state(phone)
        flow = state.get("flow")
        data = state.get("data", {})

        if flow != "RAISING_DISPUTE":
            return "Not in dispute creation flow."

        step = data.get("step", "ORDER_ID")

        if step == "ORDER_ID":
            return await self._handle_order_id(phone, body)
        elif step == "DISPUTE_TYPE":
            return await self._handle_dispute_type(phone, body, data)
        elif step == "DESCRIPTION":
            return await self._handle_description(phone, body, data)
        elif step == "CONFIRM":
            return await self._handle_confirm(phone, body, data)
        else:
            await self._state_manager.set_idle(phone)
            return "Invalid state. Starting over."

    async def _handle_order_id(self, phone: str, body: str) -> str:
        """Handle order ID input."""
        order_id = body.strip().upper()

        if not order_id or len(order_id) < 5:
            return "Please provide a valid order ID (e.g., 'ORD-12345')."

        await self._state_manager.set_state(
            phone,
            "RAISING_DISPUTE",
            {
                "step": "DISPUTE_TYPE",
                "order_id": order_id,
            },
        )

        return (
            f"📦 Order: {order_id}\n\n"
            f"What type of dispute is this?\n\n"
            f"1. Quality Issue\n"
            f"2. Delivery Problem\n"
            f"3. Payment Issue\n"
            f"4. Other\n\n"
            f"Reply with the number or describe the issue."
        )

    async def _handle_dispute_type(self, phone: str, body: str, data: Dict[str, Any]) -> str:
        """Handle dispute type input."""
        dispute_type = body.strip().lower()

        type_mapping = {
            "1": "quality",
            "quality": "quality",
            "2": "delivery",
            "delivery": "delivery",
            "3": "payment",
            "payment": "payment",
            "4": "other",
            "other": "other",
        }

        mapped_type = type_mapping.get(dispute_type, "other")

        await self._state_manager.update_state_data(
            phone,
            {"step": "DESCRIPTION", "dispute_type": mapped_type},
        )

        return (
            f"📝 Dispute Type: {mapped_type.title()}\n\n"
            f"Please describe the issue in detail:\n"
            f"• What happened?\n"
            f"• When did it happen?\n"
            f"• Any evidence (photos, receipts)?\n\n"
            f"Type your description below."
        )

    async def _handle_description(self, phone: str, body: str, data: Dict[str, Any]) -> str:
        """Handle description input."""
        description = body.strip()

        if len(description) < 10:
            return "Please provide more details about the issue (at least 10 characters)."

        await self._state_manager.update_state_data(
            phone,
            {"step": "CONFIRM", "description": description},
        )

        order_id = data.get("order_id", "Unknown")
        dispute_type = data.get("dispute_type", "Unknown")

        return (
            f"📋 *Confirm Dispute*\n\n"
            f"📦 Order: {order_id}\n"
            f"⚠️ Type: {dispute_type.title()}\n"
            f"📝 Description: {description[:100]}...\n\n"
            f"Reply 'yes' to submit this dispute or 'no' to cancel."
        )

    async def _handle_confirm(self, phone: str, body: str, data: Dict[str, Any]) -> str:
        """Handle confirmation."""
        response = body.strip().lower()

        if response in ["yes", "y", "confirm", "submit"]:
            # In production, call backend API to create dispute
            await self._state_manager.set_idle(phone)

            order_id = data.get("order_id", "Unknown")

            return (
                f"✅ *Dispute Submitted Successfully!*\n\n"
                f"Your dispute for order {order_id} has been received.\n\n"
                f"👨‍💼 An agent will review your case within 24 hours.\n\n"
                f"🔔 You'll be notified of the resolution.\n\n"
                f"Reply `menu` for more options."
            )
        elif response in ["no", "n", "cancel"]:
            await self._state_manager.set_idle(phone)
            return "❌ Dispute cancelled.\n\nReply `menu` to start over."
        else:
            return "Please reply 'yes' to submit or 'no' to cancel."
