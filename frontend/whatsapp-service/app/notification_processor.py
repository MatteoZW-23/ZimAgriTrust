"""Notification processor for WhatsApp service - handles bulk notifications."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from app.redis_client import RedisProducer
from app.whatsapp_bridge import WhatsAppBridgeClient

logger = logging.getLogger(__name__)


class NotificationProcessor:
    """Processes bulk notifications from Redis Streams."""

    def __init__(
        self,
        producer: RedisProducer,
        bridge: WhatsAppBridgeClient,
    ):
        self._producer = producer
        self._bridge = bridge

    async def process_notification(
        self,
        notification_type: str,
        target_role: str,
        data: Dict[str, Any],
        province_filter: Optional[str] = None,
    ) -> int:
        """
        Process a bulk notification.

        In production, this would:
        1. Call main backend API to get target users
        2. Send messages to all target users
        3. Track delivery status

        For now, we'll implement the logic without the API call.
        """
        logger.info(f"Processing notification type={notification_type} role={target_role}")

        # In production, fetch target users from backend API
        # For now, return 0 as we don't have access to the database
        return 0

    async def send_price_alert(
        self,
        commodity: str,
        old_price: float,
        new_price: float,
        province: Optional[str] = None,
    ) -> str:
        """Send price change alert to farmers."""
        change_pct = ((new_price - old_price) / old_price) * 100
        direction = "📈 increased" if change_pct > 0 else "📉 decreased"

        message = (
            f"💰 *Price Alert: {commodity.title()}*\n\n"
            f"Price has {direction} by {abs(change_pct):.1f}%\n"
            f"Old Price: ${old_price:.2f}/ton\n"
            f"New Price: ${new_price:.2f}/ton\n\n"
            f"Reply `prices {commodity}` for more details."
        )

        # In production, send to all farmers in the province
        # For now, just log
        logger.info(f"Price alert for {commodity}: {old_price} -> {new_price}")
        return message

    async def send_weather_alert(
        self,
        province: str,
        alert_type: str,
        message_body: str,
    ) -> str:
        """Send weather alert to farmers in specific province."""
        icons = {
            "rain": "🌧️",
            "drought": "☀️",
            "storm": "⛈️",
            "frost": "❄️",
            "heatwave": "🔥",
        }
        icon = icons.get(alert_type, "⚠️")

        message = (
            f"{icon} *Weather Alert: {province}*\n\n"
            f"{message_body}\n\n"
            f"Please take necessary precautions to protect your crops.\n\n"
            f"Reply `help` for assistance."
        )

        logger.info(f"Weather alert for {province}: {alert_type}")
        return message

    async def send_harvest_reminder(
        self,
        crop_type: str,
        province: Optional[str] = None,
    ) -> str:
        """Send harvest season reminder to farmers."""
        message = (
            f"🌾 *Harvest Season Reminder*\n\n"
            f"It's time to prepare for {crop_type.title()} harvest!\n\n"
            f"Tips:\n"
            f"• Ensure proper storage facilities\n"
            f"• Check market prices before selling\n"
            f"• Consider listing on ZimAgriTrust\n\n"
            f"Reply `sell` to list your harvest."
        )

        logger.info(f"Harvest reminder for {crop_type}")
        return message

    async def send_delivery_reminder(
        self,
        order_id: str,
        recipient_phone: str,
        days_remaining: int,
    ) -> str:
        """Send delivery reminder."""
        urgency = "🚨 URGENT" if days_remaining <= 1 else "⏰ REMINDER"

        message = (
            f"{urgency} *Delivery Reminder*\n\n"
            f"Order: {order_id}\n"
            f"Days remaining: {days_remaining}\n\n"
            f"Please ensure your delivery is on time.\n\n"
            f"Reply `help` for assistance."
        )

        await self._bridge.send_message(recipient_phone, message)
        logger.info(f"Delivery reminder sent to {recipient_phone}")
        return message

    async def send_payment_reminder(
        self,
        user_phone: str,
        amount: float,
        due_date: str,
        loan_id: str,
    ) -> str:
        """Send loan repayment reminder."""
        message = (
            f"💳 *Payment Reminder*\n\n"
            f"Loan ID: {loan_id}\n"
            f"Amount Due: ${amount:.2f}\n"
            f"Due Date: {due_date}\n\n"
            f"Please ensure timely payment to avoid penalties.\n\n"
            f"Reply `help` for payment assistance."
        )

        await self._bridge.send_message(user_phone, message)
        logger.info(f"Payment reminder sent to {user_phone}")
        return message

    async def send_verification_reminder(
        self,
        user_phone: str,
        user_name: str,
        verification_type: str,
    ) -> str:
        """Send verification reminder to users."""
        benefits = {
            "phone": "Higher trust score, more buyers",
            "id": "Increased trust score, priority listings",
            "location": "Maximum trust score, verified seller badge",
        }

        message = (
            f"🔔 *Verification Reminder*\n\n"
            f"Hi {user_name}!\n\n"
            f"Complete your {verification_type} verification to unlock:\n"
            f"• {benefits.get(verification_type, 'Better platform features')}\n\n"
            f"Reply `verify {verification_type}` to complete verification."
        )

        await self._bridge.send_message(user_phone, message)
        logger.info(f"Verification reminder sent to {user_phone}")
        return message
