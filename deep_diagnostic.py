"""
Deep System Diagnostic - تشخيص النظام العميق
=============================================

Comprehensive error detection and bug hunting:
- Log analysis for errors
- Integration testing
- Configuration validation
- Data integrity checks
- Performance anomalies
- Resource leaks
- Dead processes
"""

import asyncio
import sys
import os
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class DeepDiagnostic:
    """Deep system diagnostic tool."""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
        self.total_checks = 0
        self.failed_checks = 0

    def add_error(self, category, message, details=None):
        """Add error to report."""
        self.errors.append({
            "category": category,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        self.failed_checks += 1

    def add_warning(self, category, message, details=None):
        """Add warning to report."""
        self.warnings.append({
            "category": category,
            "message": message,
            "details": details
        })

    def add_info(self, category, message):
        """Add info to report."""
        self.info.append({
            "category": category,
            "message": message
        })

    def check(self, name):
        """Check decorator."""
        self.total_checks += 1
        print(f"\n🔍 [{self.total_checks}] {name}...")

    # ========================================
    #  Log Analysis
    # ========================================

    def analyze_logs(self):
        """Analyze system logs for errors."""
        self.check("Analyzing System Logs")

        log_paths = [
            "/home/noogh/projects/noogh_unified_system/logs/agent_daemon_startup.log",
            "/home/noogh/projects/noogh_unified_system/logs/noogh_orchestrator.log",
            "/home/noogh/projects/noogh_unified_system/logs/trading.log",
        ]

        error_patterns = [
            (r"ERROR", "Error"),
            (r"CRITICAL", "Critical"),
            (r"Exception", "Exception"),
            (r"Traceback", "Traceback"),
            (r"Failed", "Failure"),
            (r"AttributeError", "Attribute Error"),
            (r"KeyError", "Key Error"),
            (r"TypeError", "Type Error"),
            (r"ValueError", "Value Error"),
            (r"RuntimeError", "Runtime Error"),
        ]

        for log_path in log_paths:
            if not os.path.exists(log_path):
                self.add_warning("Logs", f"Log file not found: {log_path}")
                continue

            try:
                # Read last 1000 lines
                with open(log_path, 'r') as f:
                    lines = f.readlines()[-1000:]

                log_name = os.path.basename(log_path)

                # Check for errors in last 1000 lines
                for pattern, error_type in error_patterns:
                    matches = [line for line in lines if re.search(pattern, line, re.IGNORECASE)]

                    if matches:
                        # Get recent errors (last 10)
                        recent = matches[-10:]
                        self.add_error(
                            "Logs",
                            f"{error_type} found in {log_name}",
                            {"count": len(matches), "recent_samples": recent[:3]}
                        )

                print(f"   ✓ Analyzed {log_name} ({len(lines)} lines)")

            except Exception as e:
                self.add_error("Logs", f"Failed to read {log_path}", str(e))

    # ========================================
    #  Import and Module Tests
    # ========================================

    def test_critical_imports(self):
        """Test all critical module imports."""
        self.check("Testing Critical Imports")

        critical_modules = [
            ("unified_core.integration.event_bus", "EventBus"),
            ("unified_core.core.world_model", "WorldModel"),
            ("unified_core.core.neuron_fabric", "NeuronFabric"),
            ("unified_core.core.asaa", "ASAA"),
            ("unified_core.core.amla", "AMLA"),
            ("unified_core.core.consequence", "ConsequenceEngine"),
            ("unified_core.core.scar", "ScarTissue"),
            ("unified_core.observability.failure_alert_system", "FailureAlertSystem"),
            ("trading.trap_live_trader", "TrapLiveTrader"),
            ("trading.market_belief_engine", "MarketBeliefEngine"),
        ]

        for module_path, module_name in critical_modules:
            try:
                __import__(module_path)
                print(f"   ✓ {module_name}")
            except ImportError as e:
                self.add_error("Imports", f"{module_name} import failed", str(e))
            except Exception as e:
                self.add_error("Imports", f"{module_name} error", str(e))

    # ========================================
    #  Configuration Validation
    # ========================================

    def validate_configurations(self):
        """Validate system configurations."""
        self.check("Validating Configurations")

        # Check critical environment variables
        env_vars = {
            "NOOGH_TEACHER_URL": ("should be", "http://127.0.0.1:11434"),
            "RUNPOD_BRAIN_URL": ("should be empty", ""),
            "DEEPSEEK_API_KEY": ("should be empty", ""),
            "OPENAI_API_KEY": ("should be empty", ""),
        }

        for var, (description, expected) in env_vars.items():
            actual = os.environ.get(var, "NOT_SET")

            if expected == "":
                if actual not in ["", "NOT_SET"]:
                    self.add_warning(
                        "Config",
                        f"{var} {description} but is '{actual}'",
                        {"expected": expected, "actual": actual}
                    )
            else:
                if actual != expected:
                    self.add_warning(
                        "Config",
                        f"{var} {description} but is '{actual}'",
                        {"expected": expected, "actual": actual}
                    )
                else:
                    print(f"   ✓ {var}")

    # ========================================
    #  Database Integrity
    # ========================================

    async def check_database_integrity(self):
        """Check database integrity."""
        self.check("Checking Database Integrity")

        db_path = "/home/noogh/projects/noogh_unified_system/src/data/shared_memory.sqlite"

        if not os.path.exists(db_path):
            self.add_error("Database", "shared_memory.sqlite not found", db_path)
            return

        try:
            import sqlite3

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            expected_tables = ["beliefs", "predictions", "falsifications", "observations"]

            for table in expected_tables:
                if table in tables:
                    # Check row count
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"   ✓ {table}: {count} rows")
                else:
                    self.add_error("Database", f"Table '{table}' missing", None)

            # Check for corrupted data
            try:
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()
                if result[0] != "ok":
                    self.add_error("Database", "Integrity check failed", result[0])
                else:
                    print(f"   ✓ Integrity check: OK")
            except Exception as e:
                self.add_error("Database", "Integrity check error", str(e))

            conn.close()

        except Exception as e:
            self.add_error("Database", "Database check failed", str(e))

    # ========================================
    #  Process Health
    # ========================================

    def check_process_health(self):
        """Check health of running processes."""
        self.check("Checking Process Health")

        critical_processes = [
            ("agent_daemon", "Agent Daemon"),
            ("ollama", "Ollama LLM"),
        ]

        for proc_name, display_name in critical_processes:
            try:
                result = subprocess.run(
                    ['pgrep', '-f', proc_name],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    pids = result.stdout.strip().split('\n')
                    print(f"   ✓ {display_name}: Running ({len(pids)} process(es))")

                    # Check if process is zombie or unresponsive
                    for pid in pids[:3]:
                        try:
                            stat_result = subprocess.run(
                                ['ps', '-p', pid, '-o', 'state='],
                                capture_output=True,
                                text=True
                            )
                            state = stat_result.stdout.strip()

                            if state == 'Z':
                                self.add_error(
                                    "Process",
                                    f"{display_name} (PID {pid}) is zombie",
                                    None
                                )
                        except:
                            pass
                else:
                    self.add_error("Process", f"{display_name} not running", None)

            except Exception as e:
                self.add_error("Process", f"Failed to check {display_name}", str(e))

    # ========================================
    #  Memory Leaks
    # ========================================

    def check_memory_leaks(self):
        """Check for potential memory leaks."""
        self.check("Checking for Memory Leaks")

        try:
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True
            )

            python_processes = [
                line for line in result.stdout.split('\n')
                if 'python' in line.lower() and 'noogh' in line.lower()
            ]

            for proc in python_processes:
                parts = proc.split()
                if len(parts) >= 4:
                    mem_percent = float(parts[3])
                    cmd = ' '.join(parts[10:])

                    if mem_percent > 10.0:  # More than 10% memory
                        self.add_warning(
                            "Memory",
                            f"High memory usage: {mem_percent}%",
                            {"command": cmd[:100]}
                        )
                    else:
                        print(f"   ✓ {cmd[:50]}: {mem_percent}%")

        except Exception as e:
            self.add_error("Memory", "Memory check failed", str(e))

    # ========================================
    #  File Permissions
    # ========================================

    def check_file_permissions(self):
        """Check critical file permissions."""
        self.check("Checking File Permissions")

        critical_paths = [
            "/home/noogh/projects/noogh_unified_system/src/data",
            "/home/noogh/projects/noogh_unified_system/logs",
            "/home/noogh/.noogh",
        ]

        for path in critical_paths:
            if not os.path.exists(path):
                self.add_error("Permissions", f"Path does not exist: {path}", None)
                continue

            try:
                # Check read permission
                if not os.access(path, os.R_OK):
                    self.add_error("Permissions", f"No read access: {path}", None)

                # Check write permission
                if not os.access(path, os.W_OK):
                    self.add_error("Permissions", f"No write access: {path}", None)

                print(f"   ✓ {path}")

            except Exception as e:
                self.add_error("Permissions", f"Permission check failed: {path}", str(e))

    # ========================================
    #  Network Connectivity
    # ========================================

    def check_network(self):
        """Check network connectivity."""
        self.check("Checking Network Connectivity")

        # Check Ollama
        try:
            import requests
            response = requests.get('http://127.0.0.1:11434/api/tags', timeout=5)

            if response.status_code == 200:
                print(f"   ✓ Ollama API: Accessible")
            else:
                self.add_error("Network", f"Ollama API returned {response.status_code}", None)

        except requests.exceptions.ConnectionError:
            self.add_error("Network", "Cannot connect to Ollama", "http://127.0.0.1:11434")
        except Exception as e:
            self.add_error("Network", "Ollama check failed", str(e))

        # Verify no external connections
        external_check_passed = True
        for url in ["https://api.openai.com", "https://api.deepseek.com"]:
            if url in str(os.environ.values()):
                self.add_error("Network", f"External API reference found: {url}", None)
                external_check_passed = False

        if external_check_passed:
            print(f"   ✓ No external API references")

    # ========================================
    #  Integration Tests
    # ========================================

    async def test_integrations(self):
        """Test system integrations."""
        self.check("Testing System Integrations")

        # Test EventBus
        try:
            from unified_core.integration.event_bus import get_event_bus, StandardEvents
            bus = get_event_bus()

            test_received = []

            async def test_handler(event):
                test_received.append(event)

            bus.subscribe(StandardEvents.BELIEF_ADDED, test_handler, "diagnostic_test")
            await bus.publish(StandardEvents.BELIEF_ADDED, {"test": True}, "diagnostic")
            await asyncio.sleep(0.1)

            if len(test_received) > 0:
                print(f"   ✓ EventBus pub/sub working")
            else:
                self.add_error("Integration", "EventBus pub/sub not working", None)

            bus.unsubscribe(StandardEvents.BELIEF_ADDED, "diagnostic_test")

        except Exception as e:
            self.add_error("Integration", "EventBus test failed", str(e))

        # Test NeuronFabric
        try:
            from unified_core.core.neuron_fabric import get_neuron_fabric, NeuronType
            fabric = get_neuron_fabric()

            initial_count = len(fabric._neurons)

            # Create test neuron
            neuron = fabric.create_neuron(
                "diagnostic_test_neuron",
                NeuronType.COGNITIVE,
                confidence=0.5
            )

            new_count = len(fabric._neurons)

            if new_count > initial_count:
                print(f"   ✓ NeuronFabric neuron creation working")

                # Clean up
                if neuron.neuron_id in fabric._neurons:
                    del fabric._neurons[neuron.neuron_id]
            else:
                self.add_error("Integration", "NeuronFabric neuron creation failed", None)

        except Exception as e:
            self.add_error("Integration", "NeuronFabric test failed", str(e))

    # ========================================
    #  Report Generation
    # ========================================

    def generate_report(self):
        """Generate diagnostic report."""
        print("\n" + "=" * 60)
        print("📋 DIAGNOSTIC REPORT")
        print("=" * 60)

        # Summary
        print(f"\n📊 Summary:")
        print(f"   Total Checks: {self.total_checks}")
        print(f"   Errors: {len(self.errors)}")
        print(f"   Warnings: {len(self.warnings)}")
        print(f"   Info: {len(self.info)}")

        # Errors
        if self.errors:
            print(f"\n❌ ERRORS FOUND ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"\n   [{i}] {error['category']}: {error['message']}")
                if error['details']:
                    print(f"       Details: {error['details']}")
        else:
            print(f"\n✅ No errors found!")

        # Warnings
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"\n   [{i}] {warning['category']}: {warning['message']}")
                if warning['details']:
                    print(f"       Details: {warning['details']}")

        # Health Score
        if self.total_checks > 0:
            health_score = ((self.total_checks - self.failed_checks) / self.total_checks) * 100
            print(f"\n🏥 System Health Score: {health_score:.1f}%")

            if health_score >= 90:
                print(f"   Status: ✅ EXCELLENT")
            elif health_score >= 70:
                print(f"   Status: 🟡 GOOD")
            elif health_score >= 50:
                print(f"   Status: 🟠 FAIR")
            else:
                print(f"   Status: 🔴 POOR")

        print("\n" + "=" * 60)


async def main():
    """Main diagnostic function."""

    print("=" * 60)
    print("🔬 NOOGH Deep System Diagnostic")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    diagnostic = DeepDiagnostic()

    try:
        # Run all checks
        diagnostic.analyze_logs()
        diagnostic.test_critical_imports()
        diagnostic.validate_configurations()
        await diagnostic.check_database_integrity()
        diagnostic.check_process_health()
        diagnostic.check_memory_leaks()
        diagnostic.check_file_permissions()
        diagnostic.check_network()
        await diagnostic.test_integrations()

        # Generate report
        diagnostic.generate_report()

        return 0 if len(diagnostic.errors) == 0 else 1

    except Exception as e:
        print(f"\n❌ Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
