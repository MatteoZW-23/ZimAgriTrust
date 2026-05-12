"""Redis Streams producer/consumer for WhatsApp service."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional
from uuid import uuid4

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)


class RedisProducer:
    """Producer for publishing messages to Redis Streams."""

    def __init__(self, redis_client: redis.Redis):
        self._redis = redis_client

    async def publish_outbound(
        self,
        phone: str,
        message: str,
        priority: str = "normal",
    ) -> str:
        """Publish message to whatsapp:outbound stream."""
        message_id = str(uuid4())
        data = {
            "message_id": message_id,
            "phone": phone,
            "message": message,
            "timestamp": self._get_timestamp(),
            "priority": priority,
            "retry_count": 0,
        }
        await self._redis.xadd(settings.stream_outbound, data)
        logger.info(f"Published outbound message {message_id} to {phone}")
        return message_id

    async def publish_inbound(
        self,
        phone: str,
        body: str,
        has_media: bool = False,
        media: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Publish incoming message to whatsapp:inbound stream."""
        message_id = str(uuid4())
        data = {
            "message_id": message_id,
            "phone": phone,
            "body": body,
            "has_media": has_media,
            "media": json.dumps(media) if media else None,
            "timestamp": self._get_timestamp(),
        }
        await self._redis.xadd(settings.stream_inbound, data)
        logger.info(f"Published inbound message {message_id} from {phone}")
        return message_id

    async def publish_response(
        self,
        phone: str,
        response: str,
        original_message_id: Optional[str] = None,
    ) -> str:
        """Publish processed response to whatsapp:responses stream."""
        message_id = str(uuid4())
        data = {
            "message_id": message_id,
            "phone": phone,
            "response": response,
            "original_message_id": original_message_id,
            "timestamp": self._get_timestamp(),
        }
        await self._redis.xadd(settings.stream_responses, data)
        logger.info(f"Published response {message_id} for {phone}")
        return message_id

    async def publish_notification(
        self,
        notification_type: str,
        target_role: str,
        data: Dict[str, Any],
        province_filter: Optional[str] = None,
    ) -> str:
        """Publish bulk notification to whatsapp:notifications stream."""
        notification_id = str(uuid4())
        payload = {
            "notification_id": notification_id,
            "type": notification_type,
            "target_role": target_role,
            "province_filter": province_filter,
            "data": json.dumps(data),
            "timestamp": self._get_timestamp(),
        }
        await self._redis.xadd(settings.stream_notifications, payload)
        logger.info(f"Published notification {notification_id} type={notification_type}")
        return notification_id

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()


class RedisConsumer:
    """Consumer for processing messages from Redis Streams."""

    def __init__(self, redis_client: redis.Redis):
        self._redis = redis_client

    async def create_consumer_group(self, stream_name: str) -> None:
        """Create consumer group if it doesn't exist."""
        try:
            await self._redis.xgroup_create(
                stream_name,
                settings.consumer_group,
                id="0",
                mkstream=True,
            )
            logger.info(f"Created consumer group {settings.consumer_group} for {stream_name}")
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                logger.error(f"Error creating consumer group: {e}")

    async def read_outbound_messages(
        self,
        count: int = 10,
        block_ms: int = 5000,
    ) -> list[Dict[str, Any]]:
        """Read messages from whatsapp:outbound stream."""
        try:
            messages = await self._redis.xreadgroup(
                groupname=settings.consumer_group,
                consumername=settings.consumer_name,
                streams={settings.stream_outbound: ">"},
                count=count,
                block=block_ms,
            )
            if not messages:
                return []
            return self._parse_messages(messages)
        except redis.ResponseError as e:
            logger.error(f"Error reading outbound messages: {e}")
            return []

    async def read_notifications(
        self,
        count: int = 10,
        block_ms: int = 5000,
    ) -> list[Dict[str, Any]]:
        """Read messages from whatsapp:notifications stream."""
        try:
            messages = await self._redis.xreadgroup(
                groupname=settings.consumer_group,
                consumername=settings.consumer_name,
                streams={settings.stream_notifications: ">"},
                count=count,
                block=block_ms,
            )
            if not messages:
                return []
            return self._parse_messages(messages)
        except redis.ResponseError as e:
            logger.error(f"Error reading notifications: {e}")
            return []

    async def acknowledge_message(self, stream_name: str, message_id: str) -> None:
        """Acknowledge message processing."""
        await self._redis.xack(stream_name, settings.consumer_group, message_id)
        logger.debug(f"Acknowledged message {message_id} from {stream_name}")

    def _parse_messages(self, messages: list) -> list[Dict[str, Any]]:
        """Parse raw Redis Stream messages into dictionaries."""
        parsed = []
        for stream, stream_messages in messages:
            for message_id, data in stream_messages:
                parsed.append({"id": message_id, "data": data})
        return parsed


async def get_redis_client() -> redis.Redis:
    """Get async Redis client."""
    return redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
