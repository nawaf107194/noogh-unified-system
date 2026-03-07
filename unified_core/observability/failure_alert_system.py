"""
Unified Failure Alert System - نظام التنبيه الموحد عند الفشل
================================================================

يجمع جميع أنظمة المراقبة ويرسل تنبيهات عند اكتشاف فشل.

Features:
- Real-time failure detection
- Multi-channel alerts (Log, Event, Console)
- Failure severity classification
- Auto-recovery suggestions
- Integration with all monitoring systems

Usage:
    from unified_core.observability.failure_alert_system import get_failure_alert_system

    alert_system = get_failure_alert_system()
    alert_system.start_monitoring()

    # System will automatically alert on failures
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger("unified_core.observability.failure_alert")


class FailureSeverity(Enum):
    """مستوى خطورة الفشل"""
    LOW = "low"                    # بسيط - لا يؤثر على العمل
    MEDIUM = "medium"              # متوسط - قد يؤثر على بعض الوظائف
    HIGH = "high"                  # عالي - يؤثر على وظائف رئيسية
    CRITICAL = "critical"          # حرج - النظام قد يتوقف
    CATASTROPHIC = "catastrophic"  # كارثي - توقف كامل


class FailureCategory(Enum):
    """فئة الفشل"""
    SYSTEM = "system"              # فشل في النظام (CPU, Memory, etc.)
    NETWORK = "network"            # فشل في الشبكة
    DATABASE = "database"          # فشل في قاعدة البيانات
    TRADING = "trading"            # فشل في التداول
    EVOLUTION = "evolution"        # فشل في التطور
    COGNITIVE = "cognitive"        # فشل في الوظائف المعرفية
    INTEGRATION = "integration"    # فشل في التكامل


@dataclass
class FailureAlert:
    """تنبيه فشل واحد"""
    alert_id: str
    timestamp: float
    severity: FailureSeverity
    category: FailureCategory
    title: str
    message: str
    details: Dict[str, Any]
    source: str                    # أي نظام اكتشف الفشل
    suggested_action: Optional[str] = None
    auto_recoverable: bool = False
    recovery_attempted: bool = False
    resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "timestamp": self.timestamp,
            "datetime": datetime.fromtimestamp(self.timestamp).isoformat(),
            "severity": self.severity.value,
            "category": self.category.value,
            "title": self.title,
            "message": self.message,
            "details": self.details,
            "source": self.source,
            "suggested_action": self.suggested_action,
            "auto_recoverable": self.auto_recoverable,
            "recovery_attempted": self.recovery_attempted,
            "resolved": self.resolved
        }


class FailureAlertSystem:
    """
    نظام التنبيه الموحد عند الفشل

    يراقب جميع الأنظمة ويرسل تنبيهات فورية عند اكتشاف فشل.
    """

    def __init__(self):
        """Initialize Failure Alert System."""
        self.active_alerts: List[FailureAlert] = []
        self.alert_history: List[FailureAlert] = []
        self.max_history = 1000

        # Alert handlers
        self.alert_handlers: List[Callable[[FailureAlert], None]] = []

        # Monitoring state
        self.is_monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None

        # Statistics
        self.total_alerts = 0
        self.alerts_by_severity: Dict[str, int] = {s.value: 0 for s in FailureSeverity}
        self.alerts_by_category: Dict[str, int] = {c.value: 0 for c in FailureCategory}

        logger.info("🚨 Failure Alert System initialized")

    # ========================================
    #  Alert Registration
    # ========================================

    def register_alert_handler(self, handler: Callable[[FailureAlert], None]):
        """
        تسجيل معالج للتنبيهات.

        Args:
            handler: دالة تُستدعى عند كل تنبيه
        """
        self.alert_handlers.append(handler)
        logger.info(f"Alert handler registered: {handler.__name__}")

    def alert(
        self,
        severity: FailureSeverity,
        category: FailureCategory,
        title: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        source: str = "unknown",
        suggested_action: Optional[str] = None,
        auto_recoverable: bool = False
    ) -> FailureAlert:
        """
        إرسال تنبيه فشل.

        Args:
            severity: مستوى الخطورة
            category: فئة الفشل
            title: عنوان التنبيه
            message: رسالة التنبيه
            details: تفاصيل إضافية
            source: مصدر التنبيه
            suggested_action: إجراء مقترح
            auto_recoverable: هل يمكن الاستشفاء تلقائياً

        Returns:
            كائن FailureAlert
        """
        alert = FailureAlert(
            alert_id=f"alert_{int(time.time() * 1000000)}",
            timestamp=time.time(),
            severity=severity,
            category=category,
            title=title,
            message=message,
            details=details or {},
            source=source,
            suggested_action=suggested_action,
            auto_recoverable=auto_recoverable
        )

        # Add to active alerts
        self.active_alerts.append(alert)

        # Update statistics
        self.total_alerts += 1
        self.alerts_by_severity[severity.value] += 1
        self.alerts_by_category[category.value] += 1

        # Log based on severity
        self._log_alert(alert)

        # Publish event if EventBus available
        self._publish_alert_event(alert)

        # Call registered handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")

        # Auto-recovery attempt if applicable
        if auto_recoverable and not alert.recovery_attempted:
            self._attempt_auto_recovery(alert)

        return alert

    def _log_alert(self, alert: FailureAlert):
        """Log alert based on severity."""
        emoji = {
            FailureSeverity.LOW: "ℹ️",
            FailureSeverity.MEDIUM: "⚠️",
            FailureSeverity.HIGH: "🔴",
            FailureSeverity.CRITICAL: "🚨",
            FailureSeverity.CATASTROPHIC: "💥"
        }.get(alert.severity, "❓")

        log_msg = f"{emoji} [{alert.severity.value.upper()}] {alert.title}: {alert.message}"

        if alert.severity in (FailureSeverity.CATASTROPHIC, FailureSeverity.CRITICAL):
            logger.critical(log_msg)
        elif alert.severity == FailureSeverity.HIGH:
            logger.error(log_msg)
        elif alert.severity == FailureSeverity.MEDIUM:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

        if alert.suggested_action:
            logger.info(f"   💡 Suggested action: {alert.suggested_action}")

    def _publish_alert_event(self, alert: FailureAlert):
        """Publish alert to EventBus if available."""
        try:
            from unified_core.integration import get_event_bus, StandardEvents, EventPriority

            bus = get_event_bus()

            priority_map = {
                FailureSeverity.LOW: EventPriority.LOW,
                FailureSeverity.MEDIUM: EventPriority.NORMAL,
                FailureSeverity.HIGH: EventPriority.HIGH,
                FailureSeverity.CRITICAL: EventPriority.CRITICAL,
                FailureSeverity.CATASTROPHIC: EventPriority.CRITICAL
            }

            bus.publish_sync(
                StandardEvents.FAILURE_DETECTED,
                alert.to_dict(),
                "failure_alert_system",
                priority_map.get(alert.severity, EventPriority.NORMAL)
            )
        except Exception as e:
            logger.debug(f"Could not publish alert event: {e}")

    def _attempt_auto_recovery(self, alert: FailureAlert):
        """محاولة الاستشفاء التلقائي."""
        alert.recovery_attempted = True
        logger.info(f"🔄 Attempting auto-recovery for: {alert.title}")

        # TODO: Implement recovery strategies based on category
        # For now, just log
        logger.info(f"   Recovery strategy: {alert.suggested_action}")

    def resolve_alert(self, alert_id: str):
        """حل تنبيه."""
        for alert in self.active_alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                self.active_alerts.remove(alert)
                self.alert_history.append(alert)

                # Trim history if needed
                if len(self.alert_history) > self.max_history:
                    self.alert_history = self.alert_history[-self.max_history:]

                logger.info(f"✅ Alert resolved: {alert.title}")
                return True

        return False

    # ========================================
    #  Monitoring Integration
    # ========================================

    async def start_monitoring(self):
        """بدء المراقبة المستمرة."""
        if self.is_monitoring:
            logger.warning("Monitoring already running")
            return

        self.is_monitoring = True
        logger.info("🔍 Starting continuous failure monitoring...")

        # Start monitoring task
        self._monitor_task = asyncio.create_task(self._monitoring_loop())

    async def stop_monitoring(self):
        """إيقاف المراقبة."""
        self.is_monitoring = False

        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        logger.info("Monitoring stopped")

    async def _monitoring_loop(self):
        """حلقة المراقبة الرئيسية."""
        try:
            while self.is_monitoring:
                # Check all monitoring systems
                await self._check_system_health()
                await self._check_resource_usage()
                await self._check_gpu_health()
                await self._check_trading_health()
                await self._check_evolution_health()

                # Wait before next check
                await asyncio.sleep(60)  # Check every minute

        except asyncio.CancelledError:
            logger.info("Monitoring loop cancelled")
        except Exception as e:
            logger.error(f"Monitoring loop error: {e}")
            self.alert(
                FailureSeverity.HIGH,
                FailureCategory.SYSTEM,
                "Monitoring Loop Failed",
                f"Error in monitoring loop: {e}",
                source="failure_alert_system"
            )

    async def _check_system_health(self):
        """فحص صحة النظام."""
        try:
            from unified_core.health.system_health_monitor import SystemHealthMonitor

            monitor = SystemHealthMonitor()
            result = monitor.run_all_checks()

            if result['status'] == 'critical':
                self.alert(
                    FailureSeverity.CRITICAL,
                    FailureCategory.SYSTEM,
                    "System Health Critical",
                    f"System health check failed: {len(result['issues'])} issues",
                    details=result,
                    source="system_health_monitor"
                )
        except Exception as e:
            logger.debug(f"System health check failed: {e}")

    async def _check_resource_usage(self):
        """فحص استخدام الموارد."""
        try:
            import psutil

            # CPU check
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                self.alert(
                    FailureSeverity.HIGH,
                    FailureCategory.SYSTEM,
                    "High CPU Usage",
                    f"CPU usage at {cpu_percent}%",
                    details={"cpu_percent": cpu_percent},
                    source="resource_monitor",
                    suggested_action="Check for runaway processes"
                )

            # Memory check
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                self.alert(
                    FailureSeverity.HIGH,
                    FailureCategory.SYSTEM,
                    "High Memory Usage",
                    f"Memory usage at {memory.percent}%",
                    details={"memory_percent": memory.percent},
                    source="resource_monitor",
                    suggested_action="Clear cache or restart services"
                )

            # Disk check
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                self.alert(
                    FailureSeverity.CRITICAL,
                    FailureCategory.SYSTEM,
                    "Low Disk Space",
                    f"Disk usage at {disk.percent}%",
                    details={"disk_percent": disk.percent},
                    source="resource_monitor",
                    suggested_action="Clean up old files or expand storage"
                )

        except Exception as e:
            logger.debug(f"Resource check failed: {e}")

    async def _check_gpu_health(self):
        """فحص صحة GPU."""
        try:
            from unified_core.observability.gpu_monitor import get_gpu_monitor

            gpu_monitor = get_gpu_monitor()

            if not gpu_monitor.gpu_available:
                return  # No GPU to monitor

            # Check GPU metrics and generate alerts if needed
            alerts = gpu_monitor.check_and_alert()

            # Alerts are automatically sent by gpu_monitor.check_and_alert()
            # This just logs the check
            if alerts:
                logger.debug(f"GPU check generated {len(alerts)} alerts")

        except Exception as e:
            logger.debug(f"GPU check failed: {e}")

    async def _check_trading_health(self):
        """فحص صحة التداول."""
        # TODO: Check trading system health
        # - Open positions count
        # - Recent losses
        # - API connectivity
        pass

    async def _check_evolution_health(self):
        """فحص صحة التطور."""
        # TODO: Check evolution system health
        # - Recent proposals
        # - Success rate
        # - Innovation pipeline
        pass

    # ========================================
    #  Statistics & Reporting
    # ========================================

    def get_statistics(self) -> Dict[str, Any]:
        """الحصول على إحصائيات التنبيهات."""
        return {
            "total_alerts": self.total_alerts,
            "active_alerts": len(self.active_alerts),
            "resolved_alerts": len(self.alert_history),
            "by_severity": dict(self.alerts_by_severity),
            "by_category": dict(self.alerts_by_category),
            "is_monitoring": self.is_monitoring
        }

    def get_active_alerts(self, severity: Optional[FailureSeverity] = None) -> List[FailureAlert]:
        """الحصول على التنبيهات النشطة."""
        if severity:
            return [a for a in self.active_alerts if a.severity == severity]
        return self.active_alerts.copy()

    def get_critical_alerts(self) -> List[FailureAlert]:
        """الحصول على التنبيهات الحرجة فقط."""
        return [
            a for a in self.active_alerts
            if a.severity in (FailureSeverity.CRITICAL, FailureSeverity.CATASTROPHIC)
        ]


# ============================================================
#  Singleton Instance
# ============================================================

_failure_alert_system: Optional[FailureAlertSystem] = None


def get_failure_alert_system() -> FailureAlertSystem:
    """Get singleton Failure Alert System instance."""
    global _failure_alert_system
    if _failure_alert_system is None:
        _failure_alert_system = FailureAlertSystem()
    return _failure_alert_system
