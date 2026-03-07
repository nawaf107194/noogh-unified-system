"""
System Health Monitor - Prevents recurring errors
Version: 2.0.0
Created: 2026-02-24

Purpose: Continuous health checks to prevent known issues from recurring.
Updated: 2026-02-25 (Migrated to Protobuf Storage)
"""

import logging
import time
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from unified_core.evolution.innovation_storage import InnovationStorage
from proto_generated.evolution import learning_pb2

logger = logging.getLogger("unified_core.health.system_health_monitor")


class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthIssue:
    """Represents a health issue found during checks."""
    issue_type: str
    severity: HealthStatus
    message: str
    details: Dict[str, Any]
    timestamp: float
    auto_fixable: bool = False
    fix_suggestion: Optional[str] = None


class SystemHealthMonitor:
    """
    Monitors system health and prevents known issues from recurring.

    Checks:
    1. Learning → Innovation pipeline integrity
    2. Evolution Ledger health (hash chain)
    3. Innovation application rate
    4. Log file freshness
    5. Duplicate processes
    """

    def __init__(self):
        self.issues: List[HealthIssue] = []
        self.last_check_time = 0
        self.check_interval = 300  # 5 minutes
        self.storage = InnovationStorage()

    def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks and return status."""
        self.issues.clear()

        logger.info("🏥 Running system health checks...")

        # Check 1: Learning → Innovation pipeline
        self._check_learning_innovation_pipeline()

        # Check 2: Evolution Ledger integrity
        self._check_evolution_ledger_health()

        # Check 3: Innovation application rate
        self._check_innovation_application_rate()

        # Check 4: Log freshness
        self._check_log_freshness()

        # Check 5: Duplicate processes
        self._check_duplicate_processes()

        # Check 6: Innovation type coverage
        self._check_innovation_type_coverage()

        # Summarize
        status = self._get_overall_status()

        logger.info(f"✅ Health check complete: {status}")

        return {
            "status": status.value,
            "issues": [self._issue_to_dict(i) for i in self.issues],
            "timestamp": time.time(),
            "total_checks": 6,
            "checks_passed": 6 - len(set(i.issue_type for i in self.issues))
        }

    def _check_learning_innovation_pipeline(self):
        """Check if learned innovations are being applied."""
        try:
            if not os.path.exists(self.storage.pb_file):
                return

            innovations = self.storage.get_all()

            # Count by status
            suggested = sum(1 for i in innovations if i.status == learning_pb2.INNOVATION_STATUS_SUGGESTED)
            processing = sum(1 for i in innovations if i.status == learning_pb2.INNOVATION_STATUS_PROCESSING_BY_EVOLUTION)
            queued = sum(1 for i in innovations if i.status == learning_pb2.INNOVATION_STATUS_QUEUED_FOR_EVOLUTION)
            applied = sum(1 for i in innovations if i.status == learning_pb2.INNOVATION_STATUS_APPLIED)

            # Check for stagnation
            if suggested > 20:
                self.issues.append(HealthIssue(
                    issue_type="learning_stagnation",
                    severity=HealthStatus.WARNING,
                    message=f"{suggested} innovations are 'suggested' but not processed",
                    details={
                        "suggested": suggested,
                        "processing": processing,
                        "queued": queued,
                        "applied": applied
                    },
                    timestamp=time.time(),
                    auto_fixable=True,
                    fix_suggestion="Run: python scripts/apply_learning_innovations.py"
                ))

            # Check application rate
            application_rate = applied / len(innovations) if innovations else 0
            if application_rate < 0.3 and len(innovations) > 30:
                self.issues.append(HealthIssue(
                    issue_type="low_application_rate",
                    severity=HealthStatus.WARNING,
                    message=f"Only {application_rate*100:.1f}% of innovations have been applied",
                    details={
                        "application_rate": application_rate,
                        "total_innovations": len(innovations),
                        "applied": applied
                    },
                    timestamp=time.time()
                ))

        except Exception as e:
            logger.debug(f"Error checking learning pipeline: {e}")

    def _check_evolution_ledger_health(self):
        """Check Evolution Ledger for corruption."""
        try:
            from unified_core.evolution.ledger import get_evolution_ledger

            ledger = get_evolution_ledger()

            # Check if in safe mode
            if ledger.is_safe_mode():
                self.issues.append(HealthIssue(
                    issue_type="evolution_safe_mode",
                    severity=HealthStatus.CRITICAL,
                    message="Evolution Controller is in SAFE MODE due to ledger corruption",
                    details={"ledger_file": str(ledger._ledger_file)},
                    timestamp=time.time(),
                    auto_fixable=False,
                    fix_suggestion="Check ledger backups: ls -lh ~/.noogh/evolution/*.backup*"
                ))

        except Exception as e:
            logger.debug(f"Error checking ledger health: {e}")

    def _check_innovation_application_rate(self):
        """Check how often innovations are being applied."""
        try:
            if not os.path.exists(self.storage.pb_file):
                return

            innovations = self.storage.get_all()

            # Find most recent application
            applied = [i for i in innovations if i.status == learning_pb2.INNOVATION_STATUS_APPLIED and i.applied_at.seconds > 0]
            if applied:
                most_recent_sec = max(i.applied_at.seconds for i in applied)
                hours_since_last = (time.time() - most_recent_sec) / 3600

                if hours_since_last > 24:
                    self.issues.append(HealthIssue(
                        issue_type="no_recent_applications",
                        severity=HealthStatus.WARNING,
                        message=f"No innovations applied in the last {hours_since_last:.1f} hours",
                        details={"hours_since_last": hours_since_last},
                        timestamp=time.time(),
                        auto_fixable=True,
                        fix_suggestion="Trigger Evolution: check LearningInnovationTrigger"
                    ))

        except Exception as e:
            logger.debug(f"Error checking application rate: {e}")

    def _check_log_freshness(self):
        """Check if log files are being updated."""
        try:
            logs_dir = Path("logs")
            if not logs_dir.exists():
                return

            # Find most recently modified log
            log_files = list(logs_dir.glob("*.log"))
            if not log_files:
                return

            most_recent = max(log_files, key=lambda p: p.stat().st_mtime)
            age_seconds = time.time() - most_recent.stat().st_mtime
            age_hours = age_seconds / 3600

            if age_hours > 1:
                self.issues.append(HealthIssue(
                    issue_type="stale_logs",
                    severity=HealthStatus.WARNING,
                    message=f"Most recent log is {age_hours:.1f} hours old",
                    details={
                        "most_recent_log": str(most_recent),
                        "age_hours": age_hours
                    },
                    timestamp=time.time(),
                    fix_suggestion="Check if agent_daemon is running: ps aux | grep agent_daemon"
                ))

        except Exception as e:
            logger.debug(f"Error checking log freshness: {e}")

    def _check_duplicate_processes(self):
        """Check for duplicate agent_daemon processes."""
        try:
            import subprocess
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True
            )

            agent_daemon_lines = [
                line for line in result.stdout.split('\n')
                if 'agent_daemon' in line and 'grep' not in line
            ]

            if len(agent_daemon_lines) > 3:
                self.issues.append(HealthIssue(
                    issue_type="duplicate_processes",
                    severity=HealthStatus.WARNING,
                    message=f"{len(agent_daemon_lines)} agent_daemon processes running",
                    details={"process_count": len(agent_daemon_lines)},
                    timestamp=time.time(),
                    fix_suggestion="Consider stopping duplicates: killall -9 python (careful!)"
                ))

        except Exception as e:
            logger.debug(f"Error checking duplicate processes: {e}")

    def _check_innovation_type_coverage(self):
        """Check if innovation_applier supports all innovation types seen."""
        try:
            if not os.path.exists(self.storage.pb_file):
                return

            innovations = self.storage.get_all()
            
            # Get all innovation types using the string representation in context or standard
            innovation_types = set(i.context.get('original_type', str(i.innovation_type)) for i in innovations)

            # Check against supported types (from innovation_applier.py)
            supported_types = {
                'optimize_memory_queries',
                'async_parallel_scan',
                'architecture_review',
                'security_audit_enhance',
                'model_fine_tune_trigger',
                'event_loop_optimize',
                'custom_training_strategy'
            }

            # Map enums that might show up as digits if string cast is rough
            unsupported = innovation_types - supported_types
            unsupported = {u for u in unsupported if not str(u).isdigit() and u != ""}

            if unsupported:
                self.issues.append(HealthIssue(
                    issue_type="unsupported_innovation_types",
                    severity=HealthStatus.WARNING,
                    message=f"Found {len(unsupported)} unsupported innovation types",
                    details={"unsupported_types": list(unsupported)},
                    timestamp=time.time(),
                    auto_fixable=False,
                    fix_suggestion=f"Add support in innovation_applier.py for: {', '.join(unsupported)}"
                ))

        except Exception as e:
            logger.debug(f"Error checking innovation type coverage: {e}")

    def _get_overall_status(self) -> HealthStatus:
        """Determine overall health status."""
        if not self.issues:
            return HealthStatus.HEALTHY

        severities = [i.severity for i in self.issues]

        if HealthStatus.CRITICAL in severities:
            return HealthStatus.CRITICAL
        elif HealthStatus.WARNING in severities:
            return HealthStatus.WARNING
        else:
            return HealthStatus.HEALTHY

    def _issue_to_dict(self, issue: HealthIssue) -> Dict[str, Any]:
        """Convert HealthIssue to dict."""
        return {
            "type": issue.issue_type,
            "severity": issue.severity.value,
            "message": issue.message,
            "details": issue.details,
            "timestamp": issue.timestamp,
            "auto_fixable": issue.auto_fixable,
            "fix_suggestion": issue.fix_suggestion
        }


# Singleton
_monitor = None

def get_system_health_monitor() -> SystemHealthMonitor:
    """Get singleton health monitor."""
    global _monitor
    if _monitor is None:
        _monitor = SystemHealthMonitor()
    return _monitor


if __name__ == "__main__":
    # Quick health check
    monitor = get_system_health_monitor()
    result = monitor.run_all_checks()

    print("\n🏥 System Health Check Results\n")
    print(f"Status: {result['status'].upper()}\n")

    if result['issues']:
        print(f"Found {len(result['issues'])} issues:\n")
        for i, issue in enumerate(result['issues'], 1):
            print(f"{i}. [{issue['severity'].upper()}] {issue['message']}")
            if issue.get('fix_suggestion'):
                print(f"   💡 Fix: {issue['fix_suggestion']}")
            print()
    else:
        print("✅ All checks passed!")
