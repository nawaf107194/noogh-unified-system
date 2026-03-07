"""
WebSocket endpoint for real-time event streaming
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/autonomic", tags=["WebSocket Streaming"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time autonomic event streaming
    
    Usage:
        const ws = new WebSocket('ws://localhost:8000/api/v1/autonomic/ws');
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log(data.type, data.payload);
        };
    
    Events:
        - connected: Initial connection confirmation
        - observation: System observation events
        - assessment: Risk assessment events
        - proposal: Action proposal events
        - decision: Policy decision events
        - execution: Action execution events
    """
    from neural_engine.autonomic_system.websocket_manager import get_ws_manager
    
    ws_manager = get_ws_manager()
    
    # Attempt to connect
    connected = await ws_manager.connect(websocket)
    
    if not connected:
        return
    
    try:
        # Keep connection alive and listen for messages
        while True:
            # Wait for messages from client (ping/pong)
            data = await websocket.receive_text()
            
            # Handle ping
            if data == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": ""
                })
            
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info("Client disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)
