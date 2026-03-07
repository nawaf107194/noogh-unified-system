"""
NOOGH Message Bus

Async pub/sub message bus for inter-agent communication with DLQ (Dead Letter Queue).

CRITICAL: NO direct agent-to-agent communication allowed.
ALL messages MUST go through this bus.
"""

import asyncio
from collections import defaultdict
from typing import Callable, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import time

from unified_core.orchestration.messages import MessageEnvelope, MessageType, RiskLevel
from unified_core.observability import get_logger, inc_counter, set_gauge, observe_histogram

# Use structured logger
logger = get_logger("message_bus")


class MessageBus:
    """
    In-process async message bus with pub/sub pattern.
    
    Features:
    - Topic-based routing
    - Dead Letter Queue for failed messages
    - Message expiration (TTL)
    - Delivery guarantees
    """
    
    def __init__(self):
        # Subscribers: topic -> [callbacks]
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        
        # Dead Letter Queue
        self._dlq: List[MessageEnvelope] = [] # This will be updated by the new publish method to store dicts
        
        # Message history (for debugging/audit)
        self._message_history: List[MessageEnvelope] = []
        self._max_history = 1000
        
        # Stats
        self._stats = {
            "total_sent": 0,
            "total_delivered": 0,
            "total_failed": 0,
            "total_expired": 0
        }
        
        logger.info("✅ MessageBus initialized")
    
    def subscribe(self, topic: str, callback: Callable):
        """
        Subscribe to a topic.
        
        Args:
            topic: Topic name (e.g., "agent:code_executor", "event:*")
            callback: Async function to call when message arrives
        """
        self._subscribers[topic].append(callback)
        logger.info(f"Subscribed to topic: {topic}")
    
    def unsubscribe(self, topic: str, callback: Callable):
        """Unsubscribe from a topic"""
        if topic in self._subscribers:
            self._subscribers[topic].remove(callback)
            logger.info(f"Unsubscribed from topic: {topic}")
    
    async def publish(self, message: MessageEnvelope) -> bool:
        """
        Publish message to bus.
        
        Returns:
            True if delivered to at least one subscriber
        """
        self._stats["total_sent"] += 1
        
        # Check expiration
        if message.is_expired():
            logger.warning(f"Message {message.message_id} expired (TTL exceeded)")
            self._stats["total_expired"] += 1
            self._dlq.append(message)
            return False
        
        # Add to history
        self._message_history.append(message)
        if len(self._message_history) > self._max_history:
            self._message_history.pop(0)
        
        topic = message.receiver
        delivered = False
        
        # Find subscribers for the topic
        callbacks = self._subscribers.get(topic, [])
        
        if not callbacks:
            # Check for wildcard subscribers if no direct match
            # This is a simple wildcard match, could be expanded for more complex patterns
            wildcard_callbacks = []
            for sub_topic, cbs in self._subscribers.items():
                if sub_topic.endswith(".*") and topic.startswith(sub_topic[:-1]):
                    wildcard_callbacks.extend(cbs)
            callbacks.extend(wildcard_callbacks)
        
        if not callbacks:
            logger.warning(f"No subscribers for topic: {topic}. Message {message.message_id} sent to DLQ.")
            self._dlq.append(message)
            self._stats["total_failed"] += 1
            return False
        
        # Deliver to all subscribers
        delivery_tasks = []
        for callback in callbacks:
            delivery_tasks.append(self._deliver_message(callback, message))
        
        results = await asyncio.gather(*delivery_tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error delivering message {message.message_id} to a subscriber: {result}")
                self._stats["total_failed"] += 1
            else:
                delivered = True
                self._stats["total_delivered"] += 1
        
        if not delivered:
            logger.warning(f"Message {message.message_id} failed to deliver to any subscriber. Sent to DLQ.")
            self._dlq.append(message)
            return False
        
        return True
    
    async def _deliver_message(self, callback: Callable, message: MessageEnvelope):
        """Internal method to safely call a subscriber callback."""
        start_time = time.time()
        try:
            await callback(message)
            observe_histogram("message_bus_delivery_duration_seconds", time.time() - start_time, {"topic": message.receiver})
        except Exception as e:
            logger.error(f"Subscriber callback for topic '{message.receiver}' failed: {e}", exc_info=True)
            raise # Re-raise to be caught by asyncio.gather
    
    async def request_reply(
        self,
        message: MessageEnvelope,
        timeout_ms: int = 5000
    ) -> Optional[MessageEnvelope]:
        """
        Send request and wait for reply.
        
        Returns:
            Reply message or None if timeout
        """
        reply_received = asyncio.Event()
        reply_message = None
        
        def reply_callback(msg: MessageEnvelope):
            nonlocal reply_message
            if msg.trace_id == message.trace_id and msg.type == MessageType.RESULT:
                reply_message = msg
                reply_received.set()
        
        # Subscribe to reply
        self.subscribe(message.sender, reply_callback)
        
        try:
            # Send request
            await self.publish(message)
            
            # Wait for reply
            await asyncio.wait_for(
                reply_received.wait(),
                timeout=timeout_ms / 1000.0
            )
            
            return reply_message
        except asyncio.TimeoutError:
            logger.warning(f"Request {message.message_id} timed out")
            return None
        finally:
            self.unsubscribe(message.sender, reply_callback)
    
    def get_dlq(self) -> List[MessageEnvelope]:
        """Get dead letter queue messages"""
        return self._dlq.copy()
    
    def clear_dlq(self):
        """Clear dead letter queue"""
        self._dlq.clear()
    
    def get_stats(self) -> Dict[str, int]:
        """Get bus statistics"""
        return self._stats.copy()
    
    def get_history(self, limit: int = 100) -> List[MessageEnvelope]:
        """Get recent message history"""
        return self._message_history[-limit:]


# Global singleton
_bus_instance: Optional[MessageBus] = None


def get_message_bus() -> MessageBus:
    """Get or create global message bus instance"""
    global _bus_instance
    if _bus_instance is None:
        _bus_instance = MessageBus()
    return _bus_instance
