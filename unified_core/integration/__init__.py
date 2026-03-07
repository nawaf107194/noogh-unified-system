"""
NOOGH Integration Layer
=======================

البنية التحتية للتكامل بين مكونات NOOGH
Integration infrastructure for NOOGH components

Components:
-----------
- EventBus: نظام الأحداث المركزي للتواصل بين المكونات
- SystemRegistry: سجل المكونات المركزي مع إدارة الاعتماديات

Usage:
------
    from unified_core.integration import get_event_bus, get_registry

    # Event Bus
    bus = get_event_bus()
    bus.subscribe("belief_added", handler, "my_component")
    await bus.publish("belief_added", {"belief_id": "123"}, "source")

    # System Registry
    registry = get_registry()
    registry.register("world_model", world_model_instance)
    wm = registry.get("world_model")

Version: 1.0
"""

from .event_bus import (
    EventBus,
    Event,
    EventPriority,
    Subscription,
    StandardEvents,
    get_event_bus,
    subscribe_to
)

from .registry import (
    SystemRegistry,
    ComponentMetadata,
    ComponentStatus,
    get_registry,
    component
)

__all__ = [
    # EventBus
    "EventBus",
    "Event",
    "EventPriority",
    "Subscription",
    "StandardEvents",
    "get_event_bus",
    "subscribe_to",

    # Registry
    "SystemRegistry",
    "ComponentMetadata",
    "ComponentStatus",
    "get_registry",
    "component",
]

__version__ = "1.0.0"
