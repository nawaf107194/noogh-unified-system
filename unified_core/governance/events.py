"""
Observability Bus - Event System for Governance

Lightweight publish/subscribe for governance events.
Zero coupling - subscribers optional.
"""

import logging
import time
from enum import Enum
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass


logger = logging.getLogger("unified_core.governance.events")


class GovernanceEventType(Enum):
    """Event types for governance actions."""
    EXECUTION_STARTED = "execution_started"
    EXECUTION_BLOCKED = "execution_blocked"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_FAILED = "execution_failed"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_DENIED = "approval_denied"
    CIRCUIT_BREAKER_OPENED = "circuit_breaker_opened"
    STRATEGIC_CONSULTATION_REQUESTED = "strategic_consultation_requested"


@dataclass
class GovernanceEvent:
    """Governance event payload."""
    event_type: GovernanceEventType
    component: str
    user_id: Optional[str]
    timestamp: float
    metadata: Dict[str, Any]
    
    @classmethod
    def create(
        cls,
        event_type: GovernanceEventType,
        component: str,
        user_id: Optional[str] = None,
        **metadata
    ):
        """Factory method for creating events."""
        return cls(
            event_type=event_type,
            component=component,
            user_id=user_id,
            timestamp=time.time(),
            metadata=metadata
        )


class ObservabilityBus:
    """
    Lightweight event bus for governance observability.
    
    DESIGN:
    - Synchronous publish (no async complexity)
    - Fire-and-forget (no blocking)
    - Subscribers catch their own exceptions
    - No guaranteed delivery (observability, not critical path)
    """
    
    def __init__(self):
        self._subscribers: Dict[GovernanceEventType, List[Callable]] = {}
        self._global_subscribers: List[Callable] = []
    
    def subscribe(
        self,
        event_type: Optional[GovernanceEventType],
        handler: Callable[[GovernanceEvent], None]
    ):
        """
        Subscribe to events.
        
        Args:
            event_type: Specific event type, or None for all events
            handler: Callable that receives GovernanceEvent
        """
        if event_type is None:
            # Global subscriber (all events)
            self._global_subscribers.append(handler)
        else:
            # Type-specific subscriber
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(handler)
    
    def publish(self, event: GovernanceEvent):
        """
        Publish event to subscribers.
        
        SAFETY: Exceptions in handlers are caught and logged.
        """
        # Type-specific subscribers
        handlers = self._subscribers.get(event.event_type, [])
        
        # Add global subscribers
        handlers.extend(self._global_subscribers)
        
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(
                    f"Event handler failed: {handler.__name__}",
                    exc_info=True
                )


# Global singleton bus
_bus = ObservabilityBus()


def get_observability_bus() -> ObservabilityBus:
    """Get global observability bus."""
    return _bus


def publish_event(
    event_type: GovernanceEventType,
    component: str,
    user_id: Optional[str] = None,
    **metadata
):
    """Convenience function to publish events."""
    event = GovernanceEvent.create(
        event_type=event_type,
        component=component,
        user_id=user_id,
        **metadata
    )
    _bus.publish(event)


# Default audit logger (always subscribed)
def _audit_logger(event: GovernanceEvent):
    """Default audit logger for all events."""
    logger.info(
        f"[GOVERNANCE] {event.event_type.value} | "
        f"component={event.component} | "
        f"user={event.user_id} | "
        f"metadata={event.metadata}"
    )


# Subscribe audit logger to all events
_bus.subscribe(None, _audit_logger)
