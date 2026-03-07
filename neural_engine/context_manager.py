"""
Context Manager for Noug Neural OS
Tracks and maintains context across all system operations
"""

import asyncio
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ImmediateContext:
    """Current execution context"""

    user_intent: str
    entities: Dict[str, Any]
    parameters: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_intent": self.user_intent,
            "entities": self.entities,
            "parameters": self.parameters,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class HistoricalContext:
    """Historical execution context"""

    action: str
    result: Any
    success: bool
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "result": str(self.result),
            "success": self.success,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class EnvironmentalContext:
    """System and environment state"""

    system_state: Dict[str, Any]
    resource_availability: Dict[str, float]
    active_processes: List[str]
    constraints: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "system_state": self.system_state,
            "resource_availability": self.resource_availability,
            "active_processes": self.active_processes,
            "constraints": self.constraints,
            "timestamp": self.timestamp.isoformat(),
        }


class ContextManager:
    """
    Manages context across all Noug operations
    Provides unified context tracking and retrieval
    """

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history

        # Context storage
        self.immediate_context: Optional[ImmediateContext] = None
        self.historical_contexts: deque = deque(maxlen=max_history)
        self.environmental_context: Optional[EnvironmentalContext] = None

        # Session tracking
        self.session_id: Optional[str] = None
        self.session_start: Optional[datetime] = None

        # Context chains (for multi-step operations)
        self.context_chains: Dict[str, List[Dict[str, Any]]] = {}

        self._lock = asyncio.Lock()
        logger.info("ContextManager initialized")

    async def start_session(self, session_id: str):
        """Start a new context session"""
        async with self._lock:
            self.session_id = session_id
            self.session_start = datetime.now()
            logger.info(f"Started session: {session_id}")

    async def set_immediate_context(self, user_intent: str, entities: Dict[str, Any], parameters: Dict[str, Any]):
        """Set current immediate context"""
        async with self._lock:
            self.immediate_context = ImmediateContext(user_intent=user_intent, entities=entities, parameters=parameters)
            logger.info(f"Set immediate context: {user_intent}")

    async def add_historical_context(
        self, action: str, result: Any, success: bool, metadata: Optional[Dict[str, Any]] = None
    ):
        """Add to historical context"""
        async with self._lock:
            context = HistoricalContext(
                action=action, result=result, success=success, timestamp=datetime.now(), metadata=metadata or {}
            )
            self.historical_contexts.append(context)
            logger.debug(f"Added historical context: {action}")

    async def update_environmental_context(
        self,
        system_state: Dict[str, Any],
        resource_availability: Dict[str, float],
        active_processes: List[str],
        constraints: Dict[str, Any],
    ):
        """Update environmental context"""
        async with self._lock:
            self.environmental_context = EnvironmentalContext(
                system_state=system_state,
                resource_availability=resource_availability,
                active_processes=active_processes,
                constraints=constraints,
            )
            logger.debug("Updated environmental context")

    async def get_full_context(self) -> Dict[str, Any]:
        """Get complete context snapshot"""
        async with self._lock:
            return {
                "session_id": self.session_id,
                "session_start": self.session_start.isoformat() if self.session_start else None,
                "immediate": self.immediate_context.to_dict() if self.immediate_context else None,
                "historical": [ctx.to_dict() for ctx in list(self.historical_contexts)[-10:]],  # Last 10
                "environmental": self.environmental_context.to_dict() if self.environmental_context else None,
            }

    async def get_recent_history(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get recent historical contexts"""
        async with self._lock:
            recent = list(self.historical_contexts)[-count:]
            return [ctx.to_dict() for ctx in recent]

    async def get_successful_actions(self, count: int = 10) -> List[str]:
        """Get recent successful actions"""
        async with self._lock:
            successful = [ctx.action for ctx in self.historical_contexts if ctx.success]
            return successful[-count:]

    async def get_failed_actions(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent failed actions with details"""
        async with self._lock:
            failed = [
                {
                    "action": ctx.action,
                    "result": str(ctx.result),
                    "timestamp": ctx.timestamp.isoformat(),
                    "metadata": ctx.metadata,
                }
                for ctx in self.historical_contexts
                if not ctx.success
            ]
            return failed[-count:]

    async def start_context_chain(self, chain_id: str):
        """Start a new context chain for multi-step operations"""
        async with self._lock:
            self.context_chains[chain_id] = []
            logger.info(f"Started context chain: {chain_id}")

    async def add_to_chain(self, chain_id: str, step_data: Dict[str, Any]):
        """Add step to context chain"""
        async with self._lock:
            if chain_id in self.context_chains:
                self.context_chains[chain_id].append({**step_data, "timestamp": datetime.now().isoformat()})

    async def get_chain(self, chain_id: str) -> List[Dict[str, Any]]:
        """Get context chain"""
        async with self._lock:
            return self.context_chains.get(chain_id, [])

    async def end_context_chain(self, chain_id: str) -> List[Dict[str, Any]]:
        """End and return context chain"""
        async with self._lock:
            chain = self.context_chains.pop(chain_id, [])
            logger.info(f"Ended context chain: {chain_id} ({len(chain)} steps)")
            return chain

    async def clear_session(self):
        """Clear current session context"""
        async with self._lock:
            self.immediate_context = None
            self.session_id = None
            self.session_start = None
            logger.info("Cleared session context")

    async def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of current context state"""
        async with self._lock:
            total_actions = len(self.historical_contexts)
            successful = sum(1 for ctx in self.historical_contexts if ctx.success)
            failed = total_actions - successful

            return {
                "session_active": self.session_id is not None,
                "session_id": self.session_id,
                "total_actions": total_actions,
                "successful_actions": successful,
                "failed_actions": failed,
                "success_rate": (successful / total_actions * 100) if total_actions > 0 else 0,
                "active_chains": len(self.context_chains),
                "has_immediate_context": self.immediate_context is not None,
                "has_environmental_context": self.environmental_context is not None,
            }
