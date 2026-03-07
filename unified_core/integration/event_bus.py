"""
Event Bus - نظام الأحداث المركزي
Central Event System for NOOGH Integration

يوفر آلية pub/sub للتواصل بين المكونات المختلفة بدون coupling مباشر.
Provides pub/sub mechanism for component communication without tight coupling.

Version: 1.0
Author: NOOGH Integration Team
"""

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from enum import Enum

logger = logging.getLogger("unified_core.integration.event_bus")


class EventPriority(Enum):
    """أولوية الحدث"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Event:
    """
    حدث واحد في النظام
    A single event in the system
    """
    event_type: str                           # نوع الحدث (مثل "belief_added")
    data: Dict[str, Any]                      # بيانات الحدث
    source: str                               # مصدر الحدث
    priority: EventPriority = EventPriority.NORMAL
    timestamp: float = field(default_factory=time.time)
    event_id: str = field(default_factory=lambda: f"evt_{time.time_ns()}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "data": self.data,
            "source": self.source,
            "priority": self.priority.value,
            "timestamp": self.timestamp
        }


@dataclass
class Subscription:
    """
    اشتراك في نوع حدث معين
    Subscription to a specific event type
    """
    event_type: str
    handler: Callable
    subscriber_name: str
    is_async: bool = False
    filter_func: Optional[Callable[[Event], bool]] = None

    def matches(self, event: Event) -> bool:
        """تحقق إذا كان الحدث يطابق هذا الاشتراك"""
        if event.event_type != self.event_type:
            return False
        if self.filter_func and not self.filter_func(event):
            return False
        return True


class EventBus:
    """
    نظام الأحداث المركزي
    Central event bus for system-wide communication

    Features:
    - Async event handling
    - Priority-based processing
    - Event filtering
    - Event history
    - Error handling with isolation
    """

    def __init__(self, max_history: int = 1000):
        self._subscriptions: Dict[str, List[Subscription]] = defaultdict(list)
        self._event_history: List[Event] = []
        self._max_history = max_history
        self._event_counts: Dict[str, int] = defaultdict(int)
        self._handler_errors: Dict[str, int] = defaultdict(int)
        self._processing_queue: asyncio.Queue = asyncio.Queue()
        self._is_running = False

        logger.info("EventBus initialized")

    def subscribe(
        self,
        event_type: str,
        handler: Callable,
        subscriber_name: str,
        filter_func: Optional[Callable[[Event], bool]] = None
    ):
        """
        اشترك في نوع حدث معين
        Subscribe to a specific event type

        Args:
            event_type: نوع الحدث (مثل "belief_added")
            handler: الدالة التي ستُستدعى عند حدوث الحدث
            subscriber_name: اسم المشترك (للتتبع والتسجيل)
            filter_func: دالة اختيارية لتصفية الأحداث
        """
        is_async = asyncio.iscoroutinefunction(handler)

        subscription = Subscription(
            event_type=event_type,
            handler=handler,
            subscriber_name=subscriber_name,
            is_async=is_async,
            filter_func=filter_func
        )

        self._subscriptions[event_type].append(subscription)

        logger.info(
            f"📡 Subscription added: {subscriber_name} → {event_type} "
            f"(async={is_async})"
        )

    def unsubscribe(self, event_type: str, subscriber_name: str):
        """
        إلغاء الاشتراك
        Unsubscribe from event type
        """
        if event_type not in self._subscriptions:
            return

        self._subscriptions[event_type] = [
            sub for sub in self._subscriptions[event_type]
            if sub.subscriber_name != subscriber_name
        ]

        logger.info(f"Unsubscribed: {subscriber_name} from {event_type}")

    async def publish(
        self,
        event_type: str,
        data: Dict[str, Any],
        source: str,
        priority: EventPriority = EventPriority.NORMAL
    ):
        """
        نشر حدث جديد (async)
        Publish a new event

        Args:
            event_type: نوع الحدث
            data: بيانات الحدث
            source: مصدر الحدث
            priority: أولوية الحدث
        """
        event = Event(
            event_type=event_type,
            data=data,
            source=source,
            priority=priority
        )

        # حفظ في التاريخ
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        # عدّ الأحداث
        self._event_counts[event_type] += 1

        # معالجة الحدث
        await self._process_event(event)

        logger.debug(
            f"📢 Event published: {event_type} from {source} "
            f"(priority={priority.name})"
        )

    def publish_sync(
        self,
        event_type: str,
        data: Dict[str, Any],
        source: str,
        priority: EventPriority = EventPriority.NORMAL
    ):
        """
        نشر حدث (sync wrapper)
        Synchronous wrapper for publish
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # لا يوجد loop جاري - إنشاء واحد جديد
            asyncio.run(self.publish(event_type, data, source, priority))
        else:
            # loop جاري - إنشاء task
            asyncio.create_task(self.publish(event_type, data, source, priority))

    async def _process_event(self, event: Event):
        """
        معالجة حدث واحد
        Process a single event
        """
        subscriptions = self._subscriptions.get(event.event_type, [])

        if not subscriptions:
            logger.debug(f"No subscribers for {event.event_type}")
            return

        # تصفية الاشتراكات
        matching = [sub for sub in subscriptions if sub.matches(event)]

        if not matching:
            logger.debug(f"No matching subscribers for {event.event_type}")
            return

        # معالجة كل اشتراك
        tasks = []
        for subscription in matching:
            task = self._invoke_handler(subscription, event)
            tasks.append(task)

        # تشغيل كل المعالجات بالتوازي
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _invoke_handler(self, subscription: Subscription, event: Event):
        """
        استدعاء معالج حدث واحد
        Invoke a single event handler
        """
        try:
            if subscription.is_async:
                await subscription.handler(event)
            else:
                # تشغيل sync handler في executor
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, subscription.handler, event)

            logger.debug(
                f"✓ Handler executed: {subscription.subscriber_name} "
                f"for {event.event_type}"
            )

        except Exception as e:
            self._handler_errors[subscription.subscriber_name] += 1
            logger.error(
                f"✗ Handler error: {subscription.subscriber_name} "
                f"for {event.event_type}: {e}",
                exc_info=True
            )

    def get_history(
        self,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Event]:
        """
        الحصول على تاريخ الأحداث
        Get event history
        """
        history = self._event_history

        if event_type:
            history = [e for e in history if e.event_type == event_type]

        return history[-limit:]

    def get_statistics(self) -> Dict[str, Any]:
        """
        إحصائيات النظام
        Get system statistics
        """
        return {
            "total_event_types": len(self._subscriptions),
            "total_subscriptions": sum(
                len(subs) for subs in self._subscriptions.values()
            ),
            "event_counts": dict(self._event_counts),
            "handler_errors": dict(self._handler_errors),
            "history_size": len(self._event_history),
            "top_events": sorted(
                self._event_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }

    def clear_history(self):
        """مسح تاريخ الأحداث"""
        self._event_history.clear()
        logger.info("Event history cleared")

    def reset_statistics(self):
        """إعادة تعيين الإحصائيات"""
        self._event_counts.clear()
        self._handler_errors.clear()
        logger.info("Statistics reset")


# ============================================================
#  Singleton Instance
# ============================================================

_event_bus_instance: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """
    الحصول على instance وحيد للـ EventBus
    Get singleton EventBus instance
    """
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = EventBus()
    return _event_bus_instance


# ============================================================
#  Standard Event Types
# ============================================================

class StandardEvents:
    """
    أنواع الأحداث القياسية في النظام
    Standard event types in the system
    """

    # Belief Events
    BELIEF_ADDED = "belief_added"
    BELIEF_UPDATED = "belief_updated"
    BELIEF_FALSIFIED = "belief_falsified"

    # Neuron Events
    NEURON_CREATED = "neuron_created"
    NEURON_ACTIVATED = "neuron_activated"
    NEURON_PRUNED = "neuron_pruned"
    SYNAPSE_CREATED = "synapse_created"
    SYNAPSE_STRENGTHENED = "synapse_strengthened"
    SYNAPSE_WEAKENED = "synapse_weakened"

    # Decision Events
    DECISION_PROPOSED = "decision_proposed"
    DECISION_AUDITED = "decision_audited"
    DECISION_COMMITTED = "decision_committed"
    DECISION_BLOCKED = "decision_blocked"

    # Failure Events
    FAILURE_DETECTED = "failure_detected"
    SCAR_INFLICTED = "scar_inflicted"
    SCAR_HEALED = "scar_healed"

    # Task Events
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"

    # System Events
    SYSTEM_STARTED = "system_started"
    SYSTEM_STOPPED = "system_stopped"
    COMPONENT_REGISTERED = "component_registered"
    COMPONENT_UNREGISTERED = "component_unregistered"

    # Trading Events
    TRADE_SIGNAL = "trade_signal"               # New trading signal detected
    TRADE_OPENED = "trade_opened"               # Position opened
    TRADE_CLOSED = "trade_closed"               # Position closed
    TRADE_PROFIT = "trade_profit"               # Profitable trade
    TRADE_LOSS = "trade_loss"                   # Loss-making trade
    POSITION_UPDATED = "position_updated"       # Position parameters updated
    RISK_ALERT = "risk_alert"                   # Risk threshold exceeded
    MARKET_REGIME_CHANGE = "market_regime_change"  # Market regime shifted


# ============================================================
#  Helper Functions
# ============================================================

def subscribe_to(event_type: str, subscriber_name: str):
    """
    Decorator لتسهيل الاشتراك
    Decorator to simplify subscription

    Usage:
        @subscribe_to("belief_added", "world_model")
        async def on_belief_added(event: Event):
            print(f"Belief added: {event.data}")
    """
    def decorator(func):
        event_bus = get_event_bus()
        event_bus.subscribe(event_type, func, subscriber_name)
        return func
    return decorator


# ============================================================
#  Example Usage
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    async def test_event_bus():
        bus = get_event_bus()

        # مثال 1: اشتراك sync
        def on_belief_added_sync(event: Event):
            print(f"[SYNC] Belief added: {event.data}")

        bus.subscribe("belief_added", on_belief_added_sync, "test_subscriber_1")

        # مثال 2: اشتراك async
        async def on_belief_added_async(event: Event):
            print(f"[ASYNC] Belief added: {event.data}")
            await asyncio.sleep(0.1)  # محاكاة عمل async

        bus.subscribe("belief_added", on_belief_added_async, "test_subscriber_2")

        # مثال 3: اشتراك مع filter
        def filter_high_confidence(event: Event) -> bool:
            return event.data.get("confidence", 0) > 0.8

        def on_high_confidence_belief(event: Event):
            print(f"[FILTERED] High confidence belief: {event.data}")

        bus.subscribe(
            "belief_added",
            on_high_confidence_belief,
            "test_subscriber_3",
            filter_func=filter_high_confidence
        )

        # نشر أحداث
        await bus.publish(
            "belief_added",
            {"belief_id": "b123", "proposition": "Test belief", "confidence": 0.5},
            "test_source",
            EventPriority.NORMAL
        )

        await bus.publish(
            "belief_added",
            {"belief_id": "b124", "proposition": "High confidence belief", "confidence": 0.9},
            "test_source",
            EventPriority.HIGH
        )

        # انتظار المعالجة
        await asyncio.sleep(0.2)

        # عرض الإحصائيات
        stats = bus.get_statistics()
        print("\n=== Statistics ===")
        print(f"Total subscriptions: {stats['total_subscriptions']}")
        print(f"Event counts: {stats['event_counts']}")

    asyncio.run(test_event_bus())
