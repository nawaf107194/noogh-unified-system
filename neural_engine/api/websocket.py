"""
WebSocket support for real-time communication with Noug Neural OS.
"""

import asyncio
import logging
from typing import Any, Dict, List

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, client_id: str = None):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_metadata[websocket] = {
            "client_id": client_id or f"client_{len(self.active_connections)}",
            "connected_at": asyncio.get_event_loop().time(),
        }
        logger.info(f"WebSocket connected: {self.connection_metadata[websocket]['client_id']}")

    def disconnect(self, websocket: WebSocket):
            """Remove a WebSocket connection."""
            if not isinstance(websocket, WebSocket):
                raise TypeError("Expected a WebSocket object")

            if websocket in self.active_connections:
                try:
                    client_id = self.connection_metadata[websocket]["client_id"]
                    self.active_connections.remove(websocket)
                    del self.connection_metadata[websocket]
                    logger.info(f"WebSocket disconnected: {client_id}")
                except KeyError as e:
                    logger.error(f"Failed to disconnect WebSocket: Missing metadata key {e}")
                except Exception as e:
                    logger.error(f"Unexpected error while disconnecting WebSocket: {e}")
            else:
                logger.warning("Attempted to disconnect a WebSocket that was not in active connections")

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send a message to a specific client."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    async def broadcast(self, message: Dict[str, Any], exclude: WebSocket = None):
        """Broadcast a message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            if connection != exclude:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to client: {e}")
                    disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def send_to_client(self, client_id: str, message: Dict[str, Any]):
        """Send message to a specific client by ID."""
        for websocket, metadata in self.connection_metadata.items():
            if metadata["client_id"] == client_id:
                await self.send_personal_message(message, websocket)
                return True
        return False

    def get_active_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)

    def get_client_list(self) -> List[Dict[str, Any]]:
        """Get list of connected clients."""
        return [
            {"client_id": metadata["client_id"], "connected_at": metadata["connected_at"]}
            for metadata in self.connection_metadata.values()
        ]


# Global connection manager
manager = ConnectionManager()


async def handle_websocket_message(websocket: WebSocket, data: Dict[str, Any]):
    """
    Process incoming WebSocket messages.

    Message format:
    {
        "type": "process" | "memory_recall" | "subscribe" | "ping",
        "data": {...}
    }
    """
    message_type = data.get("type")
    message_data = data.get("data", {})

    try:
        if message_type == "ping":
            await manager.send_personal_message(
                {"type": "pong", "timestamp": asyncio.get_event_loop().time()}, websocket
            )

        elif message_type == "process":
            # Process input through neural system
            # This would integrate with the main processing pipeline
            response = {
                "type": "process_result",
                "data": {"status": "processing", "message": "Request received and being processed"},
            }
            await manager.send_personal_message(response, websocket)

        elif message_type == "memory_recall":
            # Recall memories
            response = {"type": "memory_result", "data": {"memories": [], "count": 0}}
            await manager.send_personal_message(response, websocket)

        elif message_type == "subscribe":
            # Subscribe to events
            channel = message_data.get("channel", "default")
            response = {"type": "subscribed", "data": {"channel": channel}}
            await manager.send_personal_message(response, websocket)

        else:
            await manager.send_personal_message(
                {"type": "error", "data": {"message": f"Unknown message type: {message_type}"}}, websocket
            )

    except Exception as e:
        logger.error(f"Error handling WebSocket message: {e}")
        await manager.send_personal_message({"type": "error", "data": {"message": str(e)}}, websocket)
