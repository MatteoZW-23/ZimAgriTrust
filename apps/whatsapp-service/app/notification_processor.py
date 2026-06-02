"""Notification processor for WhatsApp service."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings
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
        recipients = self._extract_recipients(data)
        if not recipients:
            recipients = await self._fetch_backend_recipients(target_role, province_filter)

        message = await self._build_message(notification_type, data, province_filter)
        sent_count = 0
        for recipient in recipients:
            phone = recipient.get("phone")
            if not phone:
                continue
            try:
                await self._bridge.send_message(phone, message)
                sent_count += 1
            except Exception:
                logger.exception("Failed to send WhatsApp notification to %s", phone)

        return sent_count

    async def send_price_alert(
        self,
        commodity: str,
        old_price: float,
        new_price: float,
        province: Optional[str] = None,
    ) -> str:
        change_pct = ((new_price - old_price) / old_price) * 100 if old_price else 0
        direction = "increased" if change_pct > 0 else "decreased"

        return (
            f"Price Alert: {commodity.title()}\n\n"
            f"Price has {direction} by {abs(change_pct):.1f}%\n"
            f"Old Price: ${old_price:.2f}/ton\n"
            f"New Price: ${new_price:.2f}/ton\n\n"
            f"Reply `prices {commodity}` for more details."
        )

    async def send_weather_alert(
        self,
        province: str,
        alert_type: str,
        message_body: str,
    ) -> str:
        return (
            f"Weather Alert: {province}\n\n"
            f"{alert_type.title()}: {message_body}\n\n"
            "Please take necessary precautions to protect your crops.\n\n"
            "Reply `help` for assistance."
        )

    async def send_harvest_reminder(
        self,
        crop_type: str,
        province: Optional[str] = None,
    ) -> str:
        return (
            "Harvest Season Reminder\n\n"
            f"It's time to prepare for {crop_type.title()} harvest.\n\n"
            "Tips:\n"
            "- Ensure proper storage facilities\n"
            "- Check market prices before selling\n"
            "- Consider listing on ZimAgriTrust\n\n"
            "Reply `sell` to list your harvest."
        )

    async def send_delivery_reminder(
        self,
        order_id: str,
        recipient_phone: str,
        days_remaining: int,
    ) -> str:
        urgency = "URGENT" if days_remaining <= 1 else "REMINDER"

        message = (
            f"{urgency}: Delivery Reminder\n\n"
            f"Order: {order_id}\n"
            f"Days remaining: {days_remaining}\n\n"
            "Please ensure your delivery is on time.\n\n"
            "Reply `help` for assistance."
        )

        await self._bridge.send_message(recipient_phone, message)
        return message

    async def send_payment_reminder(
        self,
        user_phone: str,
        amount: float,
        due_date: str,
        loan_id: str,
    ) -> str:
        message = (
            "Payment Reminder\n\n"
            f"Loan ID: {loan_id}\n"
            f"Amount Due: ${amount:.2f}\n"
            f"Due Date: {due_date}\n\n"
            "Please ensure timely payment to avoid penalties.\n\n"
            "Reply `help` for payment assistance."
        )

        await self._bridge.send_message(user_phone, message)
        return message

    async def send_verification_reminder(
        self,
        user_phone: str,
        user_name: str,
        verification_type: str,
    ) -> str:
        benefits = {
            "phone": "Higher trust score, more buyers",
            "id": "Increased trust score, priority listings",
            "location": "Maximum trust score, verified seller badge",
        }

        message = (
            "Verification Reminder\n\n"
            f"Hi {user_name}!\n\n"
            f"Complete your {verification_type} verification to unlock:\n"
            f"- {benefits.get(verification_type, 'Better platform features')}\n\n"
            f"Reply `verify {verification_type}` to complete verification."
        )

        await self._bridge.send_message(user_phone, message)
        return message

    async def _build_message(
        self,
        notification_type: str,
        data: Dict[str, Any],
        province_filter: Optional[str],
    ) -> str:
        if data.get("message"):
            return str(data["message"])

        if notification_type == "price_alert":
            return await self.send_price_alert(
                commodity=str(data.get("commodity", "crop")),
                old_price=float(data.get("old_price", 0)),
                new_price=float(data.get("new_price", 0)),
                province=province_filter,
            )

        if notification_type == "weather_alert":
            return await self.send_weather_alert(
                province=str(data.get("province") or province_filter or "Zimbabwe"),
                alert_type=str(data.get("alert_type", "notice")),
                message_body=str(data.get("message_body", data.get("body", ""))),
            )

        if notification_type == "harvest_reminder":
            return await self.send_harvest_reminder(
                crop_type=str(data.get("crop_type", "crop")),
                province=province_filter,
            )

        subject = str(data.get("subject", "ZimAgriTrust Update"))
        body = str(data.get("body", "Please open ZimAgriTrust for the latest update."))
        return f"{subject}\n\n{body}"

    @staticmethod
    def _extract_recipients(data: Dict[str, Any]) -> List[Dict[str, str]]:
        raw_recipients = data.get("recipients")
        if not isinstance(raw_recipients, list):
            return []

        recipients: List[Dict[str, str]] = []
        for item in raw_recipients:
            if isinstance(item, str):
                recipients.append({"phone": item})
            elif isinstance(item, dict) and item.get("phone"):
                recipients.append({"phone": str(item["phone"]), "name": str(item.get("name", ""))})
        return recipients

    async def _fetch_backend_recipients(
        self,
        target_role: str,
        province_filter: Optional[str],
    ) -> List[Dict[str, str]]:
        if not settings.internal_service_token:
            logger.error("INTERNAL_SERVICE_TOKEN is not configured for WhatsApp notifications")
            return []

        url = f"{settings.main_backend_url.rstrip('/')}/api/v1/whatsapp/recipients"
        payload = {
            "target_role": target_role.lower() if target_role else None,
            "province_filter": province_filter,
            "verified_only": True,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                json=payload,
                headers={"X-Internal-Service-Token": settings.internal_service_token},
            )
            response.raise_for_status()
            recipients = response.json().get("recipients", [])
            return recipients if isinstance(recipients, list) else []
