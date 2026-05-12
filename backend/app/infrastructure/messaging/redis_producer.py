"""Redis Streams producer for main backend - sends messages to WhatsApp service."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional
from uuid import uuid4

import redis.asyncio as redis
from sqlalchemy.orm import Session

from app.core.config import settings

logger = logging.getLogger(__name__)


class WhatsAppRedisProducer:
    """Producer for sending WhatsApp messages via Redis Streams."""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self._redis_client = redis_client
        self._stream_outbound = "whatsapp:outbound"
        self._stream_notifications = "whatsapp:notifications"

    async def _get_redis(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._redis_client is None:
            redis_url = getattr(settings, "REDIS_URL", "redis://redis:6379/0")
            self._redis_client = redis.from_url(
                redis_url, encoding="utf-8", decode_responses=True
            )
        return self._redis_client

    async def send_message(
        self,
        phone: str,
        message: str,
        priority: str = "normal",
    ) -> str:
        """Send message to WhatsApp service."""
        redis_client = await self._get_redis()
        message_id = str(uuid4())
        
        data = {
            "message_id": message_id,
            "phone": phone,
            "message": message,
            "timestamp": self._get_timestamp(),
            "priority": priority,
            "retry_count": 0,
        }
        
        try:
            await redis_client.xadd(self._stream_outbound, data)
            logger.info(f"Published WhatsApp message {message_id} to {phone}")
            return message_id
        except Exception as e:
            logger.error(f"Failed to publish WhatsApp message: {e}")
            raise

    async def send_notification(
        self,
        notification_type: str,
        target_role: str,
        data: Dict[str, Any],
        province_filter: Optional[str] = None,
    ) -> str:
        """Send bulk notification to WhatsApp service."""
        redis_client = await self._get_redis()
        notification_id = str(uuid4())
        
        payload = {
            "notification_id": notification_id,
            "type": notification_type,
            "target_role": target_role,
            "province_filter": province_filter,
            "data": json.dumps(data),
            "timestamp": self._get_timestamp(),
        }
        
        try:
            await redis_client.xadd(self._stream_notifications, payload)
            logger.info(f"Published notification {notification_id} type={notification_type}")
            return notification_id
        except Exception as e:
            logger.error(f"Failed to publish notification: {e}")
            raise

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()


# Singleton instance
_whatsapp_producer: Optional[WhatsAppRedisProducer] = None


async def get_whatsapp_producer() -> WhatsAppRedisProducer:
    """Get singleton WhatsApp Redis producer."""
    global _whatsapp_producer
    if _whatsapp_producer is None:
        _whatsapp_producer = WhatsAppRedisProducer()
    return _whatsapp_producer
