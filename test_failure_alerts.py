"""
Test Failure Alert System
==========================

Quick test to verify the unified failure alerting system works:
- Alert creation and publishing
- Severity classification
- EventBus integration
- Alert handlers
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unified_core.observability.failure_alert_system import (
    get_failure_alert_system,
    FailureSeverity,
    FailureCategory
)
from unified_core.integration.event_bus import get_event_bus, StandardEvents


def test_failure_alerts():
    """Test failure alert system."""

    print("=" * 60)
    print("Testing Failure Alert System")
    print("=" * 60)

    # Setup
    alert_system = get_failure_alert_system()
    bus = get_event_bus()

    events_received = []

    # Subscribe to failure events
    async def failure_handler(event):
        events_received.append(event.data)

    bus.subscribe(StandardEvents.FAILURE_DETECTED, failure_handler, "test_alerts")

    def wait_for_events():
        asyncio.run(asyncio.sleep(0.1))

    print("\n1. Testing LOW severity alert...")
    alert1 = alert_system.alert(
        severity=FailureSeverity.LOW,
        category=FailureCategory.SYSTEM,
        title="Minor Issue",
        message="This is a low severity test",
        details={"test": True},
        source="test_suite"
    )
    wait_for_events()
    assert alert1 is not None
    assert alert1.severity == FailureSeverity.LOW
    print(f"   Alert ID: {alert1.alert_id[:16]}...")
    print(f"   Active alerts: {len(alert_system.active_alerts)}")

    print("\n2. Testing CRITICAL severity alert...")
    alert2 = alert_system.alert(
        severity=FailureSeverity.CRITICAL,
        category=FailureCategory.TRADING,
        title="Trading System Failure",
        message="Critical trading error detected",
        details={"loss": 1000, "symbol": "BTCUSDT"},
        source="trading_monitor",
        suggested_action="Stop all trading and review positions",
        auto_recoverable=False
    )
    wait_for_events()
    assert alert2.severity == FailureSeverity.CRITICAL
    print(f"   Alert ID: {alert2.alert_id[:16]}...")
    print(f"   Suggested action: {alert2.suggested_action}")

    print("\n3. Testing CATASTROPHIC alert...")
    alert3 = alert_system.alert(
        severity=FailureSeverity.CATASTROPHIC,
        category=FailureCategory.SYSTEM,
        title="System Shutdown Imminent",
        message="Multiple critical subsystems failing",
        details={"failed_systems": ["trading", "monitoring", "memory"]},
        source="system_monitor"
    )
    wait_for_events()

    print("\n4. Testing EventBus integration...")
    assert len(events_received) >= 3, f"Expected at least 3 events, got {len(events_received)}"
    print(f"   Events published to EventBus: {len(events_received)}")

    for i, event_data in enumerate(events_received, 1):
        print(f"   Event {i}: [{event_data['severity']}] {event_data['title']}")

    print("\n5. Testing alert statistics...")
    stats = alert_system.get_statistics()
    print(f"   Total alerts: {stats['total_alerts']}")
    print(f"   Active alerts: {stats['active_alerts']}")
    print(f"   By severity: {stats['by_severity']}")
    print(f"   By category: {stats['by_category']}")

    print("\n6. Testing critical alerts filter...")
    critical_alerts = alert_system.get_critical_alerts()
    print(f"   Critical/Catastrophic alerts: {len(critical_alerts)}")
    for alert in critical_alerts:
        print(f"      - [{alert.severity.value.upper()}] {alert.title}")

    print("\n7. Testing alert resolution...")
    resolved = alert_system.resolve_alert(alert1.alert_id)
    assert resolved, "Failed to resolve alert"
    print(f"   Resolved alert: {alert1.alert_id[:16]}...")
    print(f"   Remaining active: {len(alert_system.active_alerts)}")
    print(f"   Alert history: {len(alert_system.alert_history)}")

    print("\n8. Testing custom alert handler...")
    handler_called = []

    def custom_handler(alert):
        handler_called.append(alert.title)

    alert_system.register_alert_handler(custom_handler)

    alert_system.alert(
        severity=FailureSeverity.MEDIUM,
        category=FailureCategory.NETWORK,
        title="Network Timeout",
        message="API request timed out",
        source="network_monitor"
    )

    wait_for_events()
    assert len(handler_called) >= 1, "Custom handler not called"
    print(f"   Custom handler called: {handler_called}")

    # Cleanup
    bus.unsubscribe(StandardEvents.FAILURE_DETECTED, "test_alerts")

    print("\n" + "=" * 60)
    print("Summary:")
    final_stats = alert_system.get_statistics()
    print(f"  Total alerts created: {final_stats['total_alerts']}")
    print(f"  Active alerts: {final_stats['active_alerts']}")
    print(f"  Resolved alerts: {final_stats['resolved_alerts']}")
    print(f"  EventBus events: {len(events_received)}")
    print("=" * 60)

    print("\nAll failure alert tests passed!")
    return True


async def test_continuous_monitoring():
    """Test the continuous monitoring loop (brief run)."""

    print("\n" + "=" * 60)
    print("Testing Continuous Monitoring (5 seconds)")
    print("=" * 60)

    alert_system = get_failure_alert_system()

    print("\nStarting monitoring...")
    await alert_system.start_monitoring()

    assert alert_system.is_monitoring, "Monitoring not started"
    print("Monitoring active: True")

    # Let it run briefly
    await asyncio.sleep(5)

    print("\nStopping monitoring...")
    await alert_system.stop_monitoring()

    assert not alert_system.is_monitoring, "Monitoring not stopped"
    print("Monitoring stopped: True")

    print("\nContinuous monitoring test passed!")


if __name__ == "__main__":
    try:
        # Test basic alerts
        test_failure_alerts()

        # Test continuous monitoring (brief)
        print("\n")
        asyncio.run(test_continuous_monitoring())

        print("\n" + "=" * 60)
        print("All tests completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
