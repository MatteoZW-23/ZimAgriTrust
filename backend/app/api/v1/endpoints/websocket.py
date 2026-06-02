"""
WebSocket endpoints for real-time driver tracking - Production Hardened
"""
import json
import uuid
import logging
import asyncio
from typing import Dict, Optional, Set
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.delivery_tracking_service import DeliveryTrackingService
from app.core.security import decode_token

logger = logging.getLogger(__name__)

router = APIRouter()

# Active WebSocket connections: {delivery_id: {connection_id: {"websocket": ws, "last_heartbeat": ts, "user_id": id}}}
active_connections: Dict[str, Dict[str, Dict]] = {}

# Event deduplication cache: {event_key: timestamp}
event_cache: Dict[str, datetime] = {}
EVENT_DEDUP_TTL_SECONDS = 30

# Heartbeat configuration
HEARTBEAT_INTERVAL_SECONDS = 30
HEARTBEAT_TIMEOUT_SECONDS = 90
STALE_SESSION_CLEANUP_INTERVAL_SECONDS = 60


class ConnectionManager:
    """Manages WebSocket connections for real-time tracking with production hardening"""

    def __init__(self):
        self.active_connections: Dict[str, Dict[str, Dict]] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None

    async def start_background_tasks(self):
        """Start background tasks for heartbeat monitoring and stale session cleanup"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._stale_session_cleanup_loop())
            logger.info("WebSocket stale session cleanup task started")

        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._heartbeat_monitor_loop())
            logger.info("WebSocket heartbeat monitor task started")

    async def stop_background_tasks(self):
        """Stop background tasks gracefully"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            logger.info("WebSocket stale session cleanup task stopped")

        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            logger.info("WebSocket heartbeat monitor task stopped")

    async def _stale_session_cleanup_loop(self):
        """Periodically clean up stale WebSocket sessions"""
        while True:
            try:
                await asyncio.sleep(STALE_SESSION_CLEANUP_INTERVAL_SECONDS)
                await self.cleanup_stale_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in stale session cleanup: {e}")

    async def _heartbeat_monitor_loop(self):
        """Monitor heartbeats and disconnect stale connections"""
        while True:
            try:
                await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
                await self.monitor_heartbeats()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat monitor: {e}")

    async def cleanup_stale_sessions(self):
        """Remove stale sessions based on heartbeat timeout"""
        now = datetime.now(timezone.utc)
        stale_connections = []

        for delivery_id, connections in self.active_connections.items():
            for connection_id, conn_data in connections.items():
                last_heartbeat = conn_data.get("last_heartbeat")
                if last_heartbeat:
                    age = (now - last_heartbeat).total_seconds()
                    if age > HEARTBEAT_TIMEOUT_SECONDS:
                        stale_connections.append((delivery_id, connection_id))
                        logger.warning(f"Stale session detected: delivery_id={delivery_id}, connection_id={connection_id}, age={age}s")

        for delivery_id, connection_id in stale_connections:
            await self.force_disconnect(delivery_id, connection_id, reason="heartbeat_timeout")

    async def monitor_heartbeats(self):
        """Send heartbeat pings to all active connections"""
        for delivery_id, connections in self.active_connections.items():
            for connection_id, conn_data in connections.items():
                websocket = conn_data.get("websocket")
                if websocket:
                    try:
                        await websocket.send_json({
                            "type": "heartbeat_ping",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        })
                    except Exception as e:
                        logger.error(f"Failed to send heartbeat to {connection_id}: {e}")
                        await self.force_disconnect(delivery_id, connection_id, reason="heartbeat_send_failed")

    def should_deduplicate_event(self, event_key: str) -> bool:
        """Check if event should be deduplicated (recently sent)"""
        now = datetime.now(timezone.utc)
        if event_key in event_cache:
            age = (now - event_cache[event_key]).total_seconds()
            if age < EVENT_DEDUP_TTL_SECONDS:
                return True

        event_cache[event_key] = now
        # Clean up old cache entries
        event_cache.update({k: v for k, v in event_cache.items() if (now - v).total_seconds() < EVENT_DEDUP_TTL_SECONDS * 2})
        return False

    async def connect(self, websocket: WebSocket, delivery_id: str, connection_id: str, user_id: Optional[str] = None):
        """Accept a new WebSocket connection with authentication"""
        await websocket.accept()

        if delivery_id not in self.active_connections:
            self.active_connections[delivery_id] = {}

        self.active_connections[delivery_id][connection_id] = {
            "websocket": websocket,
            "last_heartbeat": datetime.now(timezone.utc),
            "user_id": user_id,
            "connected_at": datetime.now(timezone.utc),
        }

        logger.info(f"WebSocket connected: delivery_id={delivery_id}, connection_id={connection_id}, user_id={user_id}")

        # Send initial status
        await websocket.send_json({
            "type": "connected",
            "delivery_id": delivery_id,
            "connection_id": connection_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "heartbeat_interval": HEARTBEAT_INTERVAL_SECONDS,
        })

    def disconnect(self, delivery_id: str, connection_id: str):
        """Remove a WebSocket connection"""
        if delivery_id in self.active_connections:
            if connection_id in self.active_connections[delivery_id]:
                del self.active_connections[delivery_id][connection_id]
                logger.info(f"WebSocket disconnected: delivery_id={delivery_id}, connection_id={connection_id}")

            # Clean up empty delivery groups
            if not self.active_connections[delivery_id]:
                del self.active_connections[delivery_id]

    async def force_disconnect(self, delivery_id: str, connection_id: str, reason: str = "unknown"):
        """Force disconnect a WebSocket connection with reason"""
        if delivery_id in self.active_connections and connection_id in self.active_connections[delivery_id]:
            conn_data = self.active_connections[delivery_id][connection_id]
            websocket = conn_data.get("websocket")

            try:
                await websocket.send_json({
                    "type": "disconnect",
                    "reason": reason,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=reason)
            except Exception as e:
                logger.error(f"Error during force disconnect: {e}")

            self.disconnect(delivery_id, connection_id)
            logger.warning(f"WebSocket force disconnected: delivery_id={delivery_id}, connection_id={connection_id}, reason={reason}")

    def update_heartbeat(self, delivery_id: str, connection_id: str):
        """Update last heartbeat timestamp for a connection"""
        if delivery_id in self.active_connections and connection_id in self.active_connections[delivery_id]:
            self.active_connections[delivery_id][connection_id]["last_heartbeat"] = datetime.now(timezone.utc)

    async def broadcast_to_delivery(self, delivery_id: str, message: dict, dedup_key: Optional[str] = None):
        """Broadcast a message to all connections for a delivery with deduplication"""
        # Event deduplication
        if dedup_key and self.should_deduplicate_event(dedup_key):
            logger.debug(f"Event deduplicated: {dedup_key}")
            return

        if delivery_id in self.active_connections:
            disconnected = []
            for connection_id, conn_data in self.active_connections[delivery_id].items():
                websocket = conn_data.get("websocket")
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send to connection {connection_id}: {e}")
                    disconnected.append(connection_id)

            # Clean up disconnected connections
            for connection_id in disconnected:
                await self.force_disconnect(delivery_id, connection_id, reason="send_failed")

    async def send_location_update(self, delivery_id: str, location_data: dict):
        """Send location update to all connected clients with deduplication"""
        event_key = f"location:{delivery_id}:{location_data.get('latitude')}:{location_data.get('longitude')}"
        message = {
            "type": "location_update",
            "delivery_id": delivery_id,
            "data": location_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self.broadcast_to_delivery(delivery_id, message, dedup_key=event_key)

    async def send_status_update(self, delivery_id: str, status: str, metadata: Optional[dict] = None):
        """Send status update to all connected clients with deduplication"""
        event_key = f"status:{delivery_id}:{status}"
        message = {
            "type": "status_update",
            "delivery_id": delivery_id,
            "status": status,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self.broadcast_to_delivery(delivery_id, message, dedup_key=event_key)


manager = ConnectionManager()


@router.websocket("/ws/delivery/{delivery_id}")
async def delivery_tracking_websocket(
    websocket: WebSocket,
    delivery_id: str,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    WebSocket endpoint for real-time delivery tracking with authentication

    Clients can connect to receive real-time updates:
    - Location updates
    - Status changes
    - ETA updates
    - Route deviations

    Authentication: Provide JWT token via query parameter
    Heartbeat: Server sends ping every 30s, client should respond with pong
    """
    connection_id = str(uuid.uuid4())
    user_id = None

    # Validate token if provided
    if token:
        try:
            payload = decode_token(token)
            user_id = payload.get("sub")
            logger.info(f"WebSocket authenticated: user_id={user_id}")
        except Exception as e:
            logger.warning(f"WebSocket authentication failed: {e}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="authentication_failed")
            return

    # Validate delivery exists
    from app.models.logistics import OrderDelivery
    delivery = db.query(OrderDelivery).filter(OrderDelivery.id == delivery_id).first()
    if not delivery:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Delivery not found")
        return

    # Start background tasks if not already running
    await manager.start_background_tasks()

    # Connect to WebSocket
    await manager.connect(websocket, delivery_id, connection_id, user_id)

    try:
        # Send current delivery state
        tracking_service = DeliveryTrackingService(db)
        current_location = tracking_service.get_current_location(delivery_id)

        if current_location:
            await websocket.send_json({
                "type": "initial_state",
                "delivery_id": delivery_id,
                "data": current_location,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_json()

            # Handle incoming messages from client
            message_type = data.get("type")

            if message_type == "ping" or message_type == "heartbeat_pong":
                # Update heartbeat timestamp
                manager.update_heartbeat(delivery_id, connection_id)
                # Respond to ping with pong
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

            elif message_type == "request_location":
                # Send current location
                location = tracking_service.get_current_location(delivery_id)
                if location:
                    await websocket.send_json({
                        "type": "location_update",
                        "delivery_id": delivery_id,
                        "data": location,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })

            elif message_type == "request_eta":
                # Calculate and send ETA
                eta = tracking_service.calculate_eta(delivery_id)
                await websocket.send_json({
                    "type": "eta_update",
                    "delivery_id": delivery_id,
                    "data": eta,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

            else:
                logger.warning(f"Unknown message type: {message_type}")

    except WebSocketDisconnect:
        manager.disconnect(delivery_id, connection_id)
        logger.info(f"WebSocket disconnected: delivery_id={delivery_id}, connection_id={connection_id}")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.force_disconnect(delivery_id, connection_id, reason="error")


# Helper function to broadcast location updates from other parts of the system
async def broadcast_location_update(delivery_id: str, latitude: float, longitude: float, speed_kmh: Optional[float] = None):
    """Broadcast location update to all connected clients"""
    await manager.send_location_update(delivery_id, {
        "latitude": latitude,
        "longitude": longitude,
        "speed_kmh": speed_kmh,
    })


async def broadcast_status_update(delivery_id: str, status: str, metadata: Optional[dict] = None):
    """Broadcast status update to all connected clients"""
    await manager.send_status_update(delivery_id, status, metadata)
