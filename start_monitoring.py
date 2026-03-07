"""
Start System Monitoring - بدء مراقبة النظام
============================================

Activates the unified failure alert system for continuous monitoring.

Usage:
    python start_monitoring.py

Or integrate into your main application:
    from start_monitoring import activate_monitoring
    await activate_monitoring()
"""

import asyncio
import logging
import signal
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unified_core.observability.failure_alert_system import (
    get_failure_alert_system,
    FailureSeverity,
    FailureCategory
)
from unified_core.integration.event_bus import get_event_bus, StandardEvents

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def activate_monitoring():
    """
    تفعيل نظام المراقبة الموحد
    Activate unified monitoring system
    """
    logger.info("=" * 60)
    logger.info("Activating Unified Failure Monitoring System")
    logger.info("=" * 60)

    # Get alert system
    alert_system = get_failure_alert_system()
    bus = get_event_bus()

    # Register custom alert handlers
    def console_alert_handler(alert):
        """Print critical alerts to console."""
        if alert.severity in (FailureSeverity.CRITICAL, FailureSeverity.CATASTROPHIC):
            print("\n" + "!" * 60)
            print(f"CRITICAL ALERT: {alert.title}")
            print(f"Message: {alert.message}")
            if alert.suggested_action:
                print(f"Action: {alert.suggested_action}")
            print("!" * 60 + "\n")

    def file_alert_handler(alert):
        """Log all alerts to file."""
        log_dir = "/home/noogh/.claude/projects/-home-noogh/logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "failure_alerts.log")

        with open(log_file, "a") as f:
            f.write(f"\n[{alert.timestamp}] {alert.severity.value.upper()}\n")
            f.write(f"Category: {alert.category.value}\n")
            f.write(f"Title: {alert.title}\n")
            f.write(f"Message: {alert.message}\n")
            f.write(f"Source: {alert.source}\n")
            if alert.suggested_action:
                f.write(f"Suggested Action: {alert.suggested_action}\n")
            f.write("-" * 60 + "\n")

    # Register handlers
    alert_system.register_alert_handler(console_alert_handler)
    alert_system.register_alert_handler(file_alert_handler)

    logger.info("Alert handlers registered:")
    logger.info("  - Console alerts (CRITICAL+)")
    logger.info("  - File logging (all alerts)")

    # Subscribe to EventBus for monitoring
    events_logged = {"count": 0}

    async def event_logger(event):
        events_logged["count"] += 1
        if events_logged["count"] % 100 == 0:
            logger.info(f"Events processed: {events_logged['count']}")

    bus.subscribe(StandardEvents.FAILURE_DETECTED, event_logger, "monitoring_stats")

    # Send startup alert
    alert_system.alert(
        severity=FailureSeverity.LOW,
        category=FailureCategory.SYSTEM,
        title="Monitoring System Started",
        message="Unified failure monitoring is now active",
        details={
            "version": "1.0",
            "handlers": 2,
            "monitoring_interval": "60s"
        },
        source="start_monitoring"
    )

    # Start continuous monitoring
    logger.info("\nStarting continuous monitoring loop (60s intervals)...")
    logger.info("Monitoring: System Health, Resources, Trading, Evolution")
    logger.info("Press Ctrl+C to stop\n")

    await alert_system.start_monitoring()

    return alert_system


async def main():
    """Main monitoring loop with graceful shutdown."""

    alert_system = await activate_monitoring()

    # Setup signal handlers for graceful shutdown
    shutdown_event = asyncio.Event()

    def signal_handler(signum, frame):
        logger.info("\nShutdown signal received...")
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Keep running until shutdown signal
        await shutdown_event.wait()

    except KeyboardInterrupt:
        logger.info("\nKeyboard interrupt received...")

    finally:
        logger.info("Stopping monitoring...")
        await alert_system.stop_monitoring()

        # Send shutdown alert
        alert_system.alert(
            severity=FailureSeverity.LOW,
            category=FailureCategory.SYSTEM,
            title="Monitoring System Stopped",
            message="Unified failure monitoring has been deactivated",
            source="start_monitoring"
        )

        # Show final statistics
        stats = alert_system.get_statistics()
        logger.info("\n" + "=" * 60)
        logger.info("Final Monitoring Statistics:")
        logger.info(f"  Total alerts: {stats['total_alerts']}")
        logger.info(f"  Active alerts: {stats['active_alerts']}")
        logger.info(f"  Resolved alerts: {stats['resolved_alerts']}")
        logger.info(f"  By severity: {stats['by_severity']}")
        logger.info(f"  By category: {stats['by_category']}")
        logger.info("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Monitoring system failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
