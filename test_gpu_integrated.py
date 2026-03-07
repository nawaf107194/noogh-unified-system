"""
GPU Integrated Monitoring Test - اختبار مراقبة GPU المتكاملة
===========================================================

Test GPU monitoring integrated with FailureAlertSystem.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unified_core.observability.gpu_monitor import get_gpu_monitor
from unified_core.observability.failure_alert_system import get_failure_alert_system
from unified_core.integration.event_bus import get_event_bus, StandardEvents


async def test_gpu_integrated_monitoring():
    """Test GPU monitoring with alert system."""

    print("=" * 60)
    print("🎮 GPU Integrated Monitoring Test")
    print("=" * 60)

    # Get components
    gpu_monitor = get_gpu_monitor()
    alert_system = get_failure_alert_system()
    bus = get_event_bus()

    # Track events
    events = []

    async def event_tracker(event):
        events.append(event.data)

    bus.subscribe(StandardEvents.FAILURE_DETECTED, event_tracker, "gpu_test")

    # Check GPU availability
    print("\n1️⃣ GPU Status:")
    if gpu_monitor.gpu_available:
        print(f"   ✅ {gpu_monitor.gpu_count} GPU(s) detected")
    else:
        print(f"   ⚠️  No GPU detected")

    # Get current metrics
    print("\n2️⃣ Current GPU Metrics:")
    metrics = gpu_monitor.get_metrics()

    if not metrics:
        print("   No metrics available")
    else:
        for metric in metrics:
            print(f"\n   GPU {metric.index}: {metric.name}")
            print(f"      Memory: {metric.memory_used_mb:.0f}MB / {metric.memory_total_mb:.0f}MB ({metric.memory_used_percent:.1f}%)")
            print(f"      Utilization: {metric.utilization_percent:.1f}%")
            if metric.temperature_celsius:
                print(f"      Temperature: {metric.temperature_celsius:.1f}°C")
            if metric.power_draw_watts:
                print(f"      Power: {metric.power_draw_watts:.1f}W / {metric.power_limit_watts:.1f}W ({metric.power_used_percent:.1f}%)")

    # Check and alert
    print("\n3️⃣ Checking thresholds...")
    alerts = gpu_monitor.check_and_alert()

    if alerts:
        print(f"   ⚠️  {len(alerts)} threshold violations detected:")
        for alert in alerts:
            print(f"      - [{alert['severity'].upper()}] GPU {alert['gpu_index']}: {alert['message']}")
    else:
        print("   ✅ All metrics within normal ranges")

    await asyncio.sleep(0.2)  # Wait for events to propagate

    # Get summary
    print("\n4️⃣ GPU Summary:")
    summary = gpu_monitor.get_summary()

    if summary['available']:
        print(f"   Total GPUs: {summary['count']}")
        print(f"   Total Memory: {summary['total_memory_mb']:.0f}MB")
        print(f"   Total Used: {summary['total_memory_used_mb']:.0f}MB ({summary['total_memory_used_mb']/summary['total_memory_mb']*100:.1f}%)")
        print(f"   Avg Utilization: {summary['average_utilization']:.1f}%")
        if summary['average_temperature']:
            print(f"   Avg Temperature: {summary['average_temperature']:.1f}°C")
    else:
        print(f"   {summary['message']}")

    # Alert system statistics
    print("\n5️⃣ Alert System Statistics:")
    stats = alert_system.get_statistics()
    print(f"   Total alerts: {stats['total_alerts']}")
    print(f"   Active: {stats['active_alerts']}")
    print(f"   By severity: {stats['by_severity']}")

    # Events received
    print(f"\n6️⃣ EventBus:")
    print(f"   Events received: {len(events)}")
    for event in events[-3:]:  # Show last 3
        print(f"      - [{event['severity']}] {event['title']}")

    # Test continuous monitoring (brief)
    print("\n7️⃣ Testing continuous monitoring (5 seconds)...")
    await alert_system.start_monitoring()
    print("   Monitoring started...")

    await asyncio.sleep(5)

    await alert_system.stop_monitoring()
    print("   Monitoring stopped")

    # Final stats
    final_stats = alert_system.get_statistics()
    print(f"\n   Final alert count: {final_stats['total_alerts']}")

    # Cleanup
    bus.unsubscribe(StandardEvents.FAILURE_DETECTED, "gpu_test")

    print("\n" + "=" * 60)
    print("✅ GPU Integrated Monitoring Test Complete")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(test_gpu_integrated_monitoring())
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
