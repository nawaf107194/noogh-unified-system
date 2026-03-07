"""
Event Stream API endpoints - Access autonomic events
"""

from fastapi import APIRouter, Query
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/autonomic/events", tags=["Event Streaming"])


@router.get("")
async def get_events(
    limit: int = Query(100, ge=1, le=1000),
    event_type: Optional[str] = Query(None, regex="^(observation|assessment|proposal|decision|execution)$")
) -> Dict[str, Any]:
    """
    Get recent autonomic events
    
    Args:
        limit: Maximum events to return (1-1000, default: 100)
        event_type: Filter by event type (optional)
        
    Returns:
        List of events
    """
    try:
        from neural_engine.autonomic_system.event_stream import get_event_stream
        
        stream = get_event_stream()
        events = stream.get_recent_events(limit=limit, event_type=event_type)
        
        return {
            "success": True,
            "count": len(events),
            "events": events,
            "filter": event_type
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get events: {e}")
        return {
            "success": False,
            "error": str(e),
            "events": []
        }


@router.get("/stats")
async def get_stream_stats() -> Dict[str, Any]:
    """
    Get event stream statistics
    
    Returns:
        Stream stats including counters
    """
    try:
        from neural_engine.autonomic_system.event_stream import get_event_stream
        
        stream = get_event_stream()
        stats = stream.get_stats()
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get stream stats: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/clear")
async def clear_events() -> Dict[str, Any]:
    """
    Clear all events
    
    Returns:
        Confirmation
    """
    try:
        from neural_engine.autonomic_system.event_stream import get_event_stream
        
        stream = get_event_stream()
        stream.clear()
        
        logger.info("🗑️ Events cleared via API")
        
        return {
            "success": True,
            "message": "Events cleared"
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to clear events: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/enable")
async def enable_streaming() -> Dict[str, Any]:
    """
    Enable event streaming
    
    Returns:
        Confirmation
    """
    try:
        from neural_engine.autonomic_system.event_stream import get_event_stream
        
        stream = get_event_stream()
        stream.enable()
        
        return {
            "success": True,
            "message": "Event streaming enabled"
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to enable streaming: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/disable")
async def disable_streaming() -> Dict[str, Any]:
    """
    Disable event streaming
    
    Returns:
        Confirmation
    """
    try:
        from neural_engine.autonomic_system.event_stream import get_event_stream
        
        stream = get_event_stream()
        stream.disable()
        
        return {
            "success": True,
            "message": "Event streaming disabled"
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to disable streaming: {e}")
        return {
            "success": False,
            "error": str(e)
        }
