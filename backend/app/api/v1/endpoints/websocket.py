"""
WebSocket endpoints for real-time driver tracking
"""
import json
import uuid
import logging
from typing import Dict, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.delivery_tracking_service import DeliveryTrackingService

logger = logging.getLogger(__name__)

router = APIRouter()

# Active WebSocket connections: {delivery_id: {connection_id: websocket}}
active_connections: Dict[str, Dict[str, WebSocket]] = {}


class ConnectionManager:
    """Manages WebSocket connections for real-time tracking"""
    
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, delivery_id: str, connection_id: str):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        if delivery_id not in self.active_connections:
            self.active_connections[delivery_id] = {}
        
        self.active_connections[delivery_id][connection_id] = websocket
        logger.info(f"WebSocket connected: delivery_id={delivery_id}, connection_id={connection_id}")
        
        # Send initial status
        await websocket.send_json({
            "type": "connected",
            "delivery_id": delivery_id,
            "connection_id": connection_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
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
    
    async def broadcast_to_delivery(self, delivery_id: str, message: dict):
        """Broadcast a message to all connections for a delivery"""
        if delivery_id in self.active_connections:
            disconnected = []
            for connection_id, websocket in self.active_connections[delivery_id].items():
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send to connection {connection_id}: {e}")
                    disconnected.append(connection_id)
            
            # Clean up disconnected connections
            for connection_id in disconnected:
                self.disconnect(delivery_id, connection_id)
    
    async def send_location_update(self, delivery_id: str, location_data: dict):
        """Send location update to all connected clients"""
        message = {
            "type": "location_update",
            "delivery_id": delivery_id,
            "data": location_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self.broadcast_to_delivery(delivery_id, message)
    
    async def send_status_update(self, delivery_id: str, status: str, metadata: Optional[dict] = None):
        """Send status update to all connected clients"""
        message = {
            "type": "status_update",
            "delivery_id": delivery_id,
            "status": status,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self.broadcast_to_delivery(delivery_id, message)


manager = ConnectionManager()


@router.websocket("/ws/delivery/{delivery_id}")
async def delivery_tracking_websocket(
    websocket: WebSocket,
    delivery_id: str,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    WebSocket endpoint for real-time delivery tracking
    
    Clients can connect to receive real-time updates:
    - Location updates
    - Status changes
    - ETA updates
    - Route deviations
    """
    connection_id = str(uuid.uuid4())
    
    # Validate delivery exists
    from app.models.logistics import OrderDelivery
    delivery = db.query(OrderDelivery).filter(OrderDelivery.id == delivery_id).first()
    if not delivery:
        await websocket.close(code=4001, reason="Delivery not found")
        return
    
    # Connect to WebSocket
    await manager.connect(websocket, delivery_id, connection_id)
    
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
            
            if message_type == "ping":
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
        logger.info(f"WebSocket disconnected: delivery_id={delivery_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(delivery_id, connection_id)


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
