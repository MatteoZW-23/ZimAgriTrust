"""FastAPI application for WhatsApp Service."""
from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
import redis.asyncio as redis

from app.config import settings
from app.redis_client import RedisConsumer, RedisProducer, get_redis_client
from app.whatsapp_bridge import WhatsAppBridgeClient
from app.state_manager import StateManager
from app.message_processor import MessageProcessor
from app.notification_processor import NotificationProcessor
from app.retry_handler import RetryHandler, CircuitBreaker
from app.monitoring import get_metrics_collector, get_health_checker

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    redis_client = await get_redis_client()
    consumer = RedisConsumer(redis_client)
    producer = RedisProducer(redis_client)
    bridge = WhatsAppBridgeClient()

    # Create consumer groups
    await consumer.create_consumer_group(settings.stream_outbound)
    await consumer.create_consumer_group(settings.stream_notifications)

    # Store in app state
    app.state.redis = redis_client
    app.state.consumer = consumer
    app.state.producer = producer
    app.state.bridge = bridge
    app.state.state_manager = StateManager(redis_client)
    app.state.message_processor = MessageProcessor(producer, bridge, app.state.state_manager)
    app.state.notification_processor = NotificationProcessor(producer, bridge)
    app.state.retry_handler = RetryHandler(consumer, bridge)
    app.state.circuit_breaker = CircuitBreaker()
    app.state.metrics = get_metrics_collector()
    app.state.health_checker = get_health_checker()

    # Start background tasks
    outbound_task = asyncio.create_task(
        process_outbound_messages(
            consumer,
            producer,
            bridge,
            app.state.retry_handler,
            app.state.circuit_breaker,
            app.state.metrics,
        )
    )
    notification_task = asyncio.create_task(
        process_notifications(consumer, producer, bridge, app.state.notification_processor)
    )

    app.state.outbound_task = outbound_task
    app.state.notification_task = notification_task

    logger.info("WhatsApp Service started")

    yield

    # Shutdown
    outbound_task.cancel()
    notification_task.cancel()
    await redis_client.close()
    logger.info("WhatsApp Service stopped")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return await app.state.health_checker.check_health()


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    return await app.state.health_checker.check_readiness()


@app.get("/metrics")
async def metrics():
    """Metrics endpoint for monitoring."""
    return await app.state.health_checker.get_detailed_metrics()


@app.get("/status")
async def service_status():
    """Get service status including WhatsApp Bridge status."""
    bridge = app.state.bridge
    bridge_status = await bridge.get_status()
    return {
        "service": settings.app_name,
        "whatsapp_bridge": bridge_status,
    }


async def process_outbound_messages(
    consumer: RedisConsumer,
    producer: RedisProducer,
    bridge: WhatsAppBridgeClient,
    retry_handler: RetryHandler,
    circuit_breaker: CircuitBreaker,
    metrics: Any,
):
    """Background task to process outbound messages with retry and circuit breaker."""
    logger.info("Started processing outbound messages")
    while True:
        try:
            messages = await consumer.read_outbound_messages()
            for msg in messages:
                message_id = msg["id"]
                data = msg["data"]
                phone = data["phone"]
                message = data["message"]

                logger.info(f"Processing outbound message {message_id} for {phone}")

                # Increment counter
                metrics.increment_counter("messages_received")

                # Process with circuit breaker protection
                try:
                    success = await circuit_breaker.call(
                        retry_handler.process_with_retry,
                        settings.stream_outbound,
                        message_id,
                        phone,
                        message,
                    )
                    if success:
                        metrics.increment_counter("messages_delivered")
                    else:
                        metrics.increment_counter("messages_failed")
                except Exception as e:
                    logger.error(f"Circuit breaker blocked message {message_id}: {e}")
                    metrics.increment_counter("messages_blocked")

        except asyncio.CancelledError:
            logger.info("Outbound message processing cancelled")
            break
        except Exception as e:
            logger.error(f"Error processing outbound messages: {e}")
            metrics.increment_counter("processing_errors")
            await asyncio.sleep(5)


async def process_notifications(
    consumer: RedisConsumer,
    producer: RedisProducer,
    bridge: WhatsAppBridgeClient,
    notification_processor: NotificationProcessor,
):
    """Background task to process bulk notifications."""
    logger.info("Started processing notifications")
    while True:
        try:
            messages = await consumer.read_notifications()
            for msg in messages:
                message_id = msg["id"]
                data = msg["data"]
                notification_type = data["type"]
                target_role = data.get("target_role")
                notification_data = json.loads(data.get("data", "{}"))
                province_filter = data.get("province_filter")

                logger.info(f"Processing notification {message_id} type={notification_type}")

                # Route to appropriate notification handler
                if notification_type == "price_alert":
                    await notification_processor.send_price_alert(
                        commodity=notification_data.get("commodity", ""),
                        old_price=notification_data.get("old_price", 0),
                        new_price=notification_data.get("new_price", 0),
                        province=province_filter,
                    )
                elif notification_type == "weather_alert":
                    await notification_processor.send_weather_alert(
                        province=province_filter or "",
                        alert_type=notification_data.get("alert_type", ""),
                        message_body=notification_data.get("message_body", ""),
                    )
                elif notification_type == "harvest_reminder":
                    await notification_processor.send_harvest_reminder(
                        crop_type=notification_data.get("crop_type", ""),
                        province=province_filter,
                    )
                elif notification_type == "delivery_reminder":
                    await notification_processor.send_delivery_reminder(
                        order_id=notification_data.get("order_id", ""),
                        recipient_phone=notification_data.get("recipient_phone", ""),
                        days_remaining=notification_data.get("days_remaining", 0),
                    )
                elif notification_type == "payment_reminder":
                    await notification_processor.send_payment_reminder(
                        user_phone=notification_data.get("user_phone", ""),
                        amount=notification_data.get("amount", 0),
                        due_date=notification_data.get("due_date", ""),
                        loan_id=notification_data.get("loan_id", ""),
                    )
                elif notification_type == "verification_reminder":
                    await notification_processor.send_verification_reminder(
                        user_phone=notification_data.get("user_phone", ""),
                        user_name=notification_data.get("user_name", ""),
                        verification_type=notification_data.get("verification_type", ""),
                    )

                # Acknowledge message
                await consumer.acknowledge_message(settings.stream_notifications, message_id)

        except asyncio.CancelledError:
            logger.info("Notification processing cancelled")
            break
        except Exception as e:
            logger.error(f"Error processing notifications: {e}")
            await asyncio.sleep(5)
