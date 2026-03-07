"""
Integration Example - مثال على التكامل بين Neuron Fabric و WorldModel
==================================================================

يوضح هذا المثال كيف تعمل الأحداث (Events) لربط المكونات المختلفة.

Flow:
1. WorldModel تضيف belief → ينشر حدث "belief_added"
2. NeuronFabric يستمع للحدث → ينشئ neuron تلقائياً
3. NeuronFabric ينشط neuron → ينشر حدث "neuron_activated"
4. أي مكون آخر يمكن أن يستمع لهذه الأحداث

Usage:
    python integration_example.py
"""

import asyncio
import logging
from unified_core.integration import get_event_bus, StandardEvents, Event
from unified_core.core.neuron_fabric import get_neuron_fabric
from unified_core.core.world_model import WorldModel

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_1_basic_integration():
    """
    مثال 1: التكامل الأساسي
    Basic integration between components
    """
    print("\n" + "=" * 70)
    print("Example 1: Basic Integration - التكامل الأساسي")
    print("=" * 70)

    # 1. الحصول على المكونات
    event_bus = get_event_bus()
    neuron_fabric = get_neuron_fabric()
    world_model = WorldModel()
    await world_model.setup()

    # 2. إحصائيات قبل التكامل
    stats_before = neuron_fabric.get_stats()
    print(f"\n📊 Before: {stats_before['total_neurons']} neurons")

    # 3. اشتراك NeuronFabric في أحداث WorldModel
    def on_belief_added(event: Event):
        """عند إضافة belief في WorldModel، أنشئ neuron"""
        logger.info(f"📡 Received belief_added event: {event.data['proposition'][:50]}")

        # إنشاء neuron تلقائياً
        neuron = neuron_fabric.create_neuron(
            proposition=event.data['proposition'],
            confidence=event.data['confidence'],
            domain="world_model"
        )
        logger.info(f"🧬 Auto-created neuron: {neuron.neuron_id[:8]}")

    event_bus.subscribe("belief_added", on_belief_added, "neuron_fabric")

    # 4. إضافة belief في WorldModel
    print("\n🔄 Adding belief to WorldModel...")
    belief = await world_model.add_belief(
        "النظام يعمل بشكل ممتاز",
        initial_confidence=0.85
    )

    # نشر الحدث يدوياً (سيتم تلقائياً بعد دمج WorldModel)
    await event_bus.publish(
        "belief_added",
        {
            "belief_id": belief.belief_id,
            "proposition": belief.proposition,
            "confidence": belief.confidence
        },
        "world_model"
    )

    # 5. انتظار معالجة الأحداث
    await asyncio.sleep(0.5)

    # 6. إحصائيات بعد التكامل
    stats_after = neuron_fabric.get_stats()
    print(f"\n📊 After: {stats_after['total_neurons']} neurons")
    print(f"✅ Created {stats_after['total_neurons'] - stats_before['total_neurons']} new neurons")


async def example_2_bidirectional_sync():
    """
    مثال 2: المزامنة الثنائية
    Bidirectional synchronization
    """
    print("\n" + "=" * 70)
    print("Example 2: Bidirectional Sync - المزامنة الثنائية")
    print("=" * 70)

    event_bus = get_event_bus()
    neuron_fabric = get_neuron_fabric()
    world_model = WorldModel()
    await world_model.setup()

    # اشتراك WorldModel في أحداث Neuron
    async def on_neuron_activated(event: Event):
        """عند تنشيط neuron، تحديث confidence في WorldModel"""
        logger.info(f"🎯 Neuron activated: {event.data['neuron_id'][:8]}")

        # يمكن تحديث belief confidence بناءً على activation
        if event.data['activation_level'] > 0.8:
            logger.info(f"💪 High activation detected! Updating belief confidence")

    event_bus.subscribe("neuron_activated", on_neuron_activated, "world_model")

    # إنشاء neuron وتنشيطه
    neuron = neuron_fabric.create_neuron(
        "التكامل يعمل بشكل مثالي",
        confidence=0.9
    )

    # تنشيط العصبون
    activated = neuron_fabric.activate(neuron.neuron_id, signal=1.0)

    await asyncio.sleep(0.5)

    print(f"\n✅ Activated {len(activated)} neurons")


async def example_3_event_statistics():
    """
    مثال 3: إحصائيات الأحداث
    Event statistics
    """
    print("\n" + "=" * 70)
    print("Example 3: Event Statistics - إحصائيات الأحداث")
    print("=" * 70)

    event_bus = get_event_bus()

    # الحصول على الإحصائيات
    stats = event_bus.get_statistics()

    print(f"\n📊 Event Bus Statistics:")
    print(f"  Total event types: {stats['total_event_types']}")
    print(f"  Total subscriptions: {stats['total_subscriptions']}")
    print(f"  History size: {stats['history_size']}")

    print(f"\n🔝 Top Events:")
    for event_type, count in stats['top_events'][:5]:
        print(f"  {event_type}: {count} times")


async def main():
    """تشغيل جميع الأمثلة"""
    logger.info("🚀 Starting Integration Examples")

    try:
        await example_1_basic_integration()
        await example_2_bidirectional_sync()
        await example_3_event_statistics()

        print("\n" + "=" * 70)
        print("✅ All examples completed successfully!")
        print("=" * 70)

    except Exception as e:
        logger.error(f"Error in examples: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
