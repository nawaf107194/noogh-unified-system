"""
Autonomic Event Stream - Real-time event broadcasting
Provides visibility into initiative loop decisions
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import deque
import threading

logger = logging.getLogger(__name__)


class AutonomicEvent:
    """Single event in the autonomic system"""
    
    def __init__(self, event_type: str, payload: Dict[str, Any]):
        """
        Create an event
        
        Args:
            event_type: Type of event (observation, assessment, proposal, decision, execution)
            payload: Event data
        """
        self.event_type = event_type
        self.payload = payload
        self.timestamp = datetime.now().isoformat()
        self.id = f"{event_type}_{datetime.now().timestamp()}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "type": self.event_type,
            "timestamp": self.timestamp,
            "payload": self.payload
        }


class AutonomicEventStream:
    """
    Event stream for autonomic system
    Stores events in memory with configurable buffer size
    """
    
    def __init__(self, max_events: int = 1000):
        """
        Initialize event stream
        
        Args:
            max_events: Maximum events to store (default: 1000)
        """
        self.events: deque = deque(maxlen=max_events)
        self.max_events = max_events
        self.lock = threading.Lock()
        self.enabled = True
        
        self.counters = {
            "observation": 0,
            "assessment": 0,
            "proposal": 0,
            "decision": 0,
            "execution": 0,
            "error": 0
        }
        
        logger.info(f"✅ AutonomicEventStream initialized (max_events={max_events})")
    
    def emit(self, event_type: str, payload: Dict[str, Any]):
        """
        Emit an event and broadcast to WebSocket clients
        
        Args:
            event_type: Type of event
            payload: Event data
        """
        if not self.enabled:
            return
        
        try:
            with self.lock:
                event = AutonomicEvent(event_type, payload)
                self.events.append(event)
                
                # Update counters
                if event_type in self.counters:
                    self.counters[event_type] += 1
                
                logger.debug(f"📡 Event emitted: {event_type}")
            
            # Broadcast to WebSocket / Analytics (Sync Wrapper)
            try:
                from neural_engine.autonomic_system.websocket_manager import get_ws_manager
                ws_manager = get_ws_manager()
                ws_manager.broadcast_sync(event.to_dict())
                    
            except Exception as e:
                logger.debug(f"Broadcast failed: {e}")
                
        except Exception as e:
            logger.error(f"❌ Failed to emit event: {e}")
    
    def get_recent_events(self, limit: int = 100, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get recent events
        
        Args:
            limit: Maximum number of events to return
            event_type: Filter by event type (optional)
            
        Returns:
            List of events
        """
        with self.lock:
            events = list(self.events)
            
            # Filter by type if specified
            if event_type:
                events = [e for e in events if e.event_type == event_type]
            
            # Limit and reverse (newest first)
            events = events[-limit:]
            events.reverse()
            
            return [e.to_dict() for e in events]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get streaming statistics"""
        with self.lock:
            return {
                "enabled": self.enabled,
                "total_events": len(self.events),
                "max_events": self.max_events,
                "counters": self.counters.copy()
            }
    
    def clear(self):
        """Clear all events"""
        with self.lock:
            self.events.clear()
            logger.info("🗑️ Event stream cleared")
    
    def enable(self):
        """Enable event streaming"""
        self.enabled = True
        logger.info("✅ Event streaming enabled")
    
    def disable(self):
        """Disable event streaming"""
        self.enabled = False
        logger.info("🛑 Event streaming disabled")


# Singleton instance
_stream_instance: Optional[AutonomicEventStream] = None


def get_event_stream(max_events: int = 1000) -> AutonomicEventStream:
    """Get singleton event stream"""
    global _stream_instance
    if _stream_instance is None:
        _stream_instance = AutonomicEventStream(max_events=max_events)
    return _stream_instance
