"""
WebSocket API router.

Manages real-time event streaming to connected clients.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Optional
import logging
import uuid
import asyncio
import json

from domains.websocket.events import EventFactory, BaseEvent

router = APIRouter()
logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections and broadcasts events.
    
    Features:
    - Connection lifecycle management
    - Event broadcasting to all clients
    - Automatic cleanup of dead connections
    - Client identification
    """
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.event_queue: List[BaseEvent] = []
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept new connection and send welcome message."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        
        logger.info(f"WebSocket connected: {client_id}. Total: {len(self.active_connections)}")
        
        # Send connection established event
        welcome_event = EventFactory.connection_established(client_id)
        await self.send_to_client(client_id, welcome_event)
    
    def disconnect(self, client_id: str):
        """Remove connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket disconnected: {client_id}. Total: {len(self.active_connections)}")
    
    async def send_to_client(self, client_id: str, event: BaseEvent):
        """Send event to specific client."""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(event.model_dump())
            except Exception as e:
                logger.error(f"Error sending to client {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast(self, event: BaseEvent):
        """
        Broadcast event to all connected clients.
        
        Automatically removes dead connections.
        """
        if not self.active_connections:
            return
        
        dead_connections = []
        
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_json(event.model_dump())
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                dead_connections.append(client_id)
        
        # Clean up dead connections
        for client_id in dead_connections:
            self.disconnect(client_id)
        
        logger.debug(f"Broadcasted {event.event_type} to {len(self.active_connections)} clients")
    
    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/events")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time event streaming.
    
    Protocol:
    - Client connects
    - Server sends connection_established event
    - Server broadcasts all system events
    - Client can send ping to keep alive
    """
    client_id = str(uuid.uuid4())
    
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive messages from client (mostly for keepalive)
            data = await websocket.receive_text()
            
            # Handle ping/pong for keepalive
            if data == "ping":
                await websocket.send_json({"type": "pong", "timestamp": None})
            
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        manager.disconnect(client_id)


def broadcast_event(event: BaseEvent):
    """
    Synchronous wrapper for broadcasting events.
    
    Use this from sync code to broadcast events.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(manager.broadcast(event))
        else:
            loop.run_until_complete(manager.broadcast(event))
    except Exception as e:
        logger.error(f"Failed to broadcast event: {e}")


async def broadcast_event_async(event: BaseEvent):
    """Async wrapper for broadcasting events."""
    await manager.broadcast(event)
