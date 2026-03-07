"""
GPU Monitor - مراقب GPU
========================

Continuous GPU monitoring with alerting integration.
Monitors memory, utilization, temperature, and power.
"""

import logging
import time
import subprocess
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger("unified_core.observability.gpu_monitor")


@dataclass
class GPUMetrics:
    """GPU metrics snapshot."""
    index: int
    name: str
    memory_total_mb: float
    memory_used_mb: float
    memory_free_mb: float
    utilization_percent: float
    temperature_celsius: Optional[float]
    power_draw_watts: Optional[float]
    power_limit_watts: Optional[float]
    timestamp: float

    @property
    def memory_used_percent(self) -> float:
        return (self.memory_used_mb / self.memory_total_mb * 100) if self.memory_total_mb > 0 else 0.0

    @property
    def power_used_percent(self) -> float:
        if self.power_draw_watts and self.power_limit_watts and self.power_limit_watts > 0:
            return (self.power_draw_watts / self.power_limit_watts * 100)
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "name": self.name,
            "memory_total_mb": self.memory_total_mb,
            "memory_used_mb": self.memory_used_mb,
            "memory_free_mb": self.memory_free_mb,
            "memory_used_percent": self.memory_used_percent,
            "utilization_percent": self.utilization_percent,
            "temperature_celsius": self.temperature_celsius,
            "power_draw_watts": self.power_draw_watts,
            "power_limit_watts": self.power_limit_watts,
            "power_used_percent": self.power_used_percent,
            "timestamp": self.timestamp
        }


class GPUMonitor:
    """
    مراقب GPU - GPU Monitor

    Monitors GPU metrics and triggers alerts on threshold violations.
    """

    def __init__(
        self,
        memory_warning_threshold: float = 80.0,
        memory_critical_threshold: float = 90.0,
        temp_warning_threshold: float = 80.0,
        temp_critical_threshold: float = 85.0,
        utilization_high_threshold: float = 95.0
    ):
        """
        Initialize GPU Monitor.

        Args:
            memory_warning_threshold: Memory % for warning alert
            memory_critical_threshold: Memory % for critical alert
            temp_warning_threshold: Temperature °C for warning
            temp_critical_threshold: Temperature °C for critical
            utilization_high_threshold: Utilization % threshold
        """
        self.memory_warning_threshold = memory_warning_threshold
        self.memory_critical_threshold = memory_critical_threshold
        self.temp_warning_threshold = temp_warning_threshold
        self.temp_critical_threshold = temp_critical_threshold
        self.utilization_high_threshold = utilization_high_threshold

        self.gpu_available = self._check_gpu_availability()
        self.gpu_count = 0

        if self.gpu_available:
            self.gpu_count = self._get_gpu_count()
            logger.info(f"🎮 GPU Monitor initialized: {self.gpu_count} GPU(s) found")
        else:
            logger.warning("⚠️  No GPU detected - monitoring disabled")

    def _check_gpu_availability(self) -> bool:
        """Check if nvidia-smi is available."""
        try:
            result = subprocess.run(
                ['nvidia-smi', '-L'],
                capture_output=True,
                timeout=2
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _get_gpu_count(self) -> int:
        """Get number of GPUs."""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=count', '--format=csv,noheader'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0 and result.stdout.strip():
                # nvidia-smi returns the same count for each GPU, so just get first line
                return len(result.stdout.strip().split('\n'))
            return 0
        except Exception as e:
            logger.error(f"Failed to get GPU count: {e}")
            return 0

    def get_metrics(self) -> List[GPUMetrics]:
        """
        Get current GPU metrics for all GPUs.

        Returns:
            List of GPUMetrics for each GPU
        """
        if not self.gpu_available:
            return []

        metrics = []

        try:
            result = subprocess.run(
                ['nvidia-smi',
                 '--query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu,power.draw,power.limit',
                 '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                logger.error("nvidia-smi command failed")
                return []

            timestamp = time.time()

            for line in result.stdout.strip().split('\n'):
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 7:
                    try:
                        metric = GPUMetrics(
                            index=int(parts[0]),
                            name=parts[1],
                            memory_total_mb=float(parts[2]),
                            memory_used_mb=float(parts[3]),
                            memory_free_mb=float(parts[4]),
                            utilization_percent=float(parts[5]),
                            temperature_celsius=float(parts[6]) if parts[6] not in ['[N/A]', '[Not Supported]'] else None,
                            power_draw_watts=float(parts[7]) if len(parts) > 7 and parts[7] not in ['[N/A]', '[Not Supported]'] else None,
                            power_limit_watts=float(parts[8]) if len(parts) > 8 and parts[8] not in ['[N/A]', '[Not Supported]'] else None,
                            timestamp=timestamp
                        )
                        metrics.append(metric)
                    except ValueError as e:
                        logger.error(f"Failed to parse GPU metrics: {e}")
                        continue

        except subprocess.TimeoutExpired:
            logger.error("nvidia-smi timeout")
        except Exception as e:
            logger.error(f"Failed to get GPU metrics: {e}")

        return metrics

    def check_and_alert(self) -> List[Dict[str, Any]]:
        """
        Check GPU metrics and generate alerts if thresholds are exceeded.

        Returns:
            List of alert dictionaries
        """
        metrics = self.get_metrics()
        alerts = []

        try:
            from unified_core.observability.failure_alert_system import (
                get_failure_alert_system,
                FailureSeverity,
                FailureCategory
            )
            alert_system = get_failure_alert_system()
        except ImportError:
            logger.warning("FailureAlertSystem not available")
            alert_system = None

        for metric in metrics:
            # Memory alerts
            mem_percent = metric.memory_used_percent

            if mem_percent >= self.memory_critical_threshold:
                alert = {
                    "severity": "critical",
                    "gpu_index": metric.index,
                    "type": "memory",
                    "message": f"GPU {metric.index} memory at {mem_percent:.1f}%",
                    "details": metric.to_dict()
                }
                alerts.append(alert)

                if alert_system:
                    alert_system.alert(
                        FailureSeverity.CRITICAL,
                        FailureCategory.SYSTEM,
                        f"GPU {metric.index} Memory Critical",
                        f"{metric.name} memory at {mem_percent:.1f}%",
                        details=metric.to_dict(),
                        source="gpu_monitor",
                        suggested_action="Free GPU memory or reduce batch size"
                    )

            elif mem_percent >= self.memory_warning_threshold:
                alert = {
                    "severity": "high",
                    "gpu_index": metric.index,
                    "type": "memory",
                    "message": f"GPU {metric.index} memory at {mem_percent:.1f}%",
                    "details": metric.to_dict()
                }
                alerts.append(alert)

                if alert_system:
                    alert_system.alert(
                        FailureSeverity.HIGH,
                        FailureCategory.SYSTEM,
                        f"GPU {metric.index} Memory High",
                        f"{metric.name} memory at {mem_percent:.1f}%",
                        details=metric.to_dict(),
                        source="gpu_monitor"
                    )

            # Temperature alerts
            if metric.temperature_celsius:
                if metric.temperature_celsius >= self.temp_critical_threshold:
                    alert = {
                        "severity": "critical",
                        "gpu_index": metric.index,
                        "type": "temperature",
                        "message": f"GPU {metric.index} temperature at {metric.temperature_celsius:.1f}°C",
                        "details": metric.to_dict()
                    }
                    alerts.append(alert)

                    if alert_system:
                        alert_system.alert(
                            FailureSeverity.CRITICAL,
                            FailureCategory.SYSTEM,
                            f"GPU {metric.index} Overheating",
                            f"{metric.name} temperature at {metric.temperature_celsius:.1f}°C",
                            details=metric.to_dict(),
                            source="gpu_monitor",
                            suggested_action="Check cooling system, reduce load, or shutdown"
                        )

                elif metric.temperature_celsius >= self.temp_warning_threshold:
                    alert = {
                        "severity": "high",
                        "gpu_index": metric.index,
                        "type": "temperature",
                        "message": f"GPU {metric.index} temperature at {metric.temperature_celsius:.1f}°C",
                        "details": metric.to_dict()
                    }
                    alerts.append(alert)

                    if alert_system:
                        alert_system.alert(
                            FailureSeverity.HIGH,
                            FailureCategory.SYSTEM,
                            f"GPU {metric.index} Temperature High",
                            f"{metric.name} temperature at {metric.temperature_celsius:.1f}°C",
                            details=metric.to_dict(),
                            source="gpu_monitor"
                        )

            # Utilization alerts (informational)
            if metric.utilization_percent >= self.utilization_high_threshold:
                alert = {
                    "severity": "medium",
                    "gpu_index": metric.index,
                    "type": "utilization",
                    "message": f"GPU {metric.index} utilization at {metric.utilization_percent:.1f}%",
                    "details": metric.to_dict()
                }
                alerts.append(alert)

        return alerts

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all GPU metrics."""
        if not self.gpu_available:
            return {
                "available": False,
                "count": 0,
                "message": "No GPU detected"
            }

        metrics = self.get_metrics()

        return {
            "available": True,
            "count": len(metrics),
            "gpus": [m.to_dict() for m in metrics],
            "total_memory_mb": sum(m.memory_total_mb for m in metrics),
            "total_memory_used_mb": sum(m.memory_used_mb for m in metrics),
            "average_utilization": sum(m.utilization_percent for m in metrics) / len(metrics) if metrics else 0,
            "average_temperature": sum(m.temperature_celsius for m in metrics if m.temperature_celsius) / len([m for m in metrics if m.temperature_celsius]) if any(m.temperature_celsius for m in metrics) else None
        }


# ============================================================
#  Singleton Instance
# ============================================================

_gpu_monitor: Optional[GPUMonitor] = None


def get_gpu_monitor() -> GPUMonitor:
    """Get singleton GPU Monitor instance."""
    global _gpu_monitor
    if _gpu_monitor is None:
        _gpu_monitor = GPUMonitor()
    return _gpu_monitor
