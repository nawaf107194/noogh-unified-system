"""
WebSocket Event Streaming - Real-time push notifications
Broadcasts autonomic events to connected clients
"""

import logging
import json
from typing import Set, Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections for event streaming
    """
    
    def __init__(self, max_clients: int = 5):
        """
        Initialize WebSocket manager
        
        Args:
            max_clients: Maximum concurrent connections (default: 5)
        """
        self.active_connections: Set[WebSocket] = set()
        self.max_clients = max_clients
        self.message_count = 0
        
        logger.info(f"✅ WebSocketManager initialized (max_clients={max_clients})")
    
    async def connect(self, websocket: WebSocket) -> bool:
        """
        Connect a new client
        
        Args:
            websocket: WebSocket connection
            
        Returns:
            True if connected, False if rejected
        """
        if len(self.active_connections) >= self.max_clients:
            logger.warning(f"🚫 Connection rejected (max clients: {self.max_clients})")
            await websocket.close(code=1008, reason="Max clients reached")
            return False
        
        await websocket.accept()
        self.active_connections.add(websocket)
        
        logger.info(f"✅ Client connected (total: {len(self.active_connections)})")
        
        # Send welcome message
        await self._send_to_client(websocket, {
            "type": "connected",
            "timestamp": datetime.now().isoformat(),
            "message": "Connected to NOOGH Autonomic Event Stream"
        })
        
        return True
    
    def disconnect(self, websocket: WebSocket):
        """
        Disconnect a client
        
        Args:
            websocket: WebSocket connection
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"🔌 Client disconnected (remaining: {len(self.active_connections)})")
    
    async def broadcast(self, event: Dict[str, Any]):
        """
        Broadcast event to all connected clients
        
        Args:
            event: Event to broadcast
        """
        if not self.active_connections:
            # Even if no clients connected, still feed analytics
            self._feed_analytics(event)
            return
        
        self.message_count += 1
        
        # Prepare message
        message = {
            "type": event.get("type", "unknown"),
            "timestamp": event.get("timestamp", datetime.now().isoformat()),
            "payload": event.get("payload", {}),
            "id": event.get("id", f"event_{self.message_count}")
        }
        
        # Feed analytics with this event
        self._feed_analytics(message)
        
        # Send to all clients
        disconnected = set()
        for connection in self.active_connections:
            try:
                await self._send_to_client(connection, message)
            except Exception as e:
                logger.error(f"❌ Failed to send to client: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected clients
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    def broadcast_sync(self, event: Dict[str, Any]):
        """
        Synchronous broadcast wrapper for threads
        Always feeds analytics, then attempts async broadcast if loop available
        """
        # 1. Feed analytics immediately (Sync)
        self._feed_analytics(event)
        
        # 2. Schedule async broadcast if in event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.broadcast(event))
        except RuntimeError:
            # No loop in this thread, try to find main thread loop?
            # For now, we skip WS broadcast in non-async threads if no loop provided
            # ideally use run_coroutine_threadsafe if we had reference to main loop
            pass

    
    def _feed_analytics(self, event: Dict[str, Any]):
        """Feed event to analytics KPI calculator"""
        try:
            # First try direct import assuming we are in the gateway context
            try:
                from gateway.app.analytics.kpi_calculator import get_kpi_calculator
                kpi_calc = get_kpi_calculator()
                kpi_calc.add_event(event)
                logger.debug(f"📊 Event fed to GLOBAL gateway analytics: {event.get('type')}")
                return
            except ImportError:
                pass

            # Fallback (legacy) - try to find path
            import sys
            import os
            
            # Add src to path if possible
            current_dir = os.path.dirname(__file__)
            src_path = os.path.abspath(os.path.join(current_dir, '../../../'))
            if src_path not in sys.path:
                sys.path.insert(0, src_path)
            
            from gateway.app.analytics.kpi_calculator import get_kpi_calculator
            
            kpi_calc = get_kpi_calculator()
            kpi_calc.add_event(event)
            
            logger.debug(f"📊 Event fed to analytics (via src path): {event.get('type')}")
        except Exception as e:
            logger.warning(f"Failed to feed analytics: {e}")

    
    async def _send_to_client(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to a single client"""
        await websocket.send_json(message)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket statistics"""
        return {
            "active_connections": len(self.active_connections),
            "max_clients": self.max_clients,
            "messages_sent": self.message_count
        }


# Singleton instance
_ws_manager: Optional[WebSocketManager] = None


def get_ws_manager() -> WebSocketManager:
    """Get singleton WebSocket manager"""
    global _ws_manager
    if _ws_manager is None:
        _ws_manager = WebSocketManager()
    return _ws_manager
