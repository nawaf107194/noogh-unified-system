"""
Live Monitoring Test - اختبار المراقبة المباشرة
================================================

Tests the monitoring system with real checks and simulated failures.
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


async def test_live_monitoring():
    """Test live monitoring with real system checks."""

    print("=" * 60)
    print("🔍 Live Monitoring Test - Real System Checks")
    print("=" * 60)

    alert_system = get_failure_alert_system()
    bus = get_event_bus()

    events = []

    async def event_tracker(event):
        events.append(event.data)
        print(f"\n📡 Event: [{event.data['severity']}] {event.data['title']}")

    bus.subscribe(StandardEvents.FAILURE_DETECTED, event_tracker, "live_test")

    print("\n1️⃣ Checking current system state...")

    try:
        import psutil

        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        print(f"\n📊 System Resources:")
        print(f"   CPU: {cpu:.1f}%")
        print(f"   Memory: {memory.percent:.1f}% ({memory.used / 1024**3:.1f}GB / {memory.total / 1024**3:.1f}GB)")
        print(f"   Disk: {disk.percent:.1f}% ({disk.used / 1024**3:.1f}GB / {disk.total / 1024**3:.1f}GB)")

        if cpu > 80:
            alert_system.alert(
                FailureSeverity.HIGH,
                FailureCategory.SYSTEM,
                "High CPU Usage Detected",
                f"CPU at {cpu:.1f}%",
                details={"cpu_percent": cpu},
                source="live_monitor"
            )

        if memory.percent > 80:
            alert_system.alert(
                FailureSeverity.HIGH,
                FailureCategory.SYSTEM,
                "High Memory Usage Detected",
                f"Memory at {memory.percent:.1f}%",
                details={"memory_percent": memory.percent},
                source="live_monitor"
            )

        if disk.percent > 80:
            alert_system.alert(
                FailureSeverity.CRITICAL,
                FailureCategory.SYSTEM,
                "High Disk Usage Detected",
                f"Disk at {disk.percent:.1f}%",
                details={"disk_percent": disk.percent},
                source="live_monitor"
            )

    except Exception as e:
        print(f"⚠️  Resource check failed: {e}")

    print("\n2️⃣ Testing simulated trading failures...")

    alert_system.alert(
        FailureSeverity.CRITICAL,
        FailureCategory.TRADING,
        "Large Trading Loss",
        "Position closed with -$1,250 loss (-12.5%)",
        details={"symbol": "BTCUSDT", "pnl": -1250, "pnl_percent": -12.5},
        source="trading_simulator",
        suggested_action="Review risk management and position sizing"
    )

    await asyncio.sleep(0.1)

    alert_system.alert(
        FailureSeverity.HIGH,
        FailureCategory.NETWORK,
        "Exchange API Connection Failed",
        "Unable to connect to Binance API - timeout after 30s",
        details={"exchange": "Binance", "timeout": 30},
        source="api_monitor",
        suggested_action="Check network connectivity and API status"
    )

    await asyncio.sleep(0.1)

    alert_system.alert(
        FailureSeverity.MEDIUM,
        FailureCategory.TRADING,
        "Strategy Win Rate Below Target",
        "TrendFollower strategy at 28% win rate (target: 45%)",
        details={"strategy": "TrendFollower", "win_rate": 0.28, "target": 0.45},
        source="performance_monitor",
        suggested_action="Pause strategy and analyze recent trades"
    )

    await asyncio.sleep(0.1)

    print("\n3️⃣ Checking system health...")

    try:
        from unified_core.health.system_health_monitor import SystemHealthMonitor
        monitor = SystemHealthMonitor()
        result = monitor.run_all_checks()

        print(f"\n🏥 System Health: {result['status']}")
        print(f"   Checks passed: {result['checks_passed']}/{result['total_checks']}")

        if result['issues']:
            print(f"   ⚠️  Issues found: {len(result['issues'])}")
            for issue in result['issues'][:3]:
                print(f"      - {issue}")
            
    except Exception as e:
        print(f"⚠️  System health check failed: {e}")

    print("\n" + "=" * 60)
    print("Test Completed Successfully")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_live_monitoring())
