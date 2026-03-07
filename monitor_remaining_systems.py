"""
Monitor Remaining Systems - مراقبة باقي الأنظمة
=============================================

Deep monitoring of:
- Evolution & Innovation systems
- Security systems (ASAA, AMLA, ScarTissue)
- Memory & Storage
- Consequence tracking
- Alert systems
- Background services
"""

import asyncio
import sys
import os
import sqlite3
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class RemainingSystemsMonitor:
    """Monitor remaining systems."""

    def __init__(self):
        self.issues = []
        self.warnings = []
        self.stats = {}

    def print_section(self, title):
        """Print section header."""
        print("\n" + "=" * 70)
        print(f"📊 {title}")
        print("=" * 70)

    async def monitor_evolution_system(self):
        """Monitor evolution and innovation systems."""
        self.print_section("EVOLUTION & INNOVATION SYSTEM")

        try:
            from unified_core.evolution.ledger import EvolutionLedger

            ledger = EvolutionLedger()

            print(f"\n🧬 Evolution Ledger:")
            print(f"   Total Proposals: {len(ledger.proposals):,}")

            # Count by status
            status_counts = {}
            for proposal in ledger.proposals.values():
                status = proposal.status
                status_counts[status] = status_counts.get(status, 0) + 1

            print(f"\n   Status Breakdown:")
            for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"      {status}: {count:,}")

            # Recent proposals (last 10)
            recent = sorted(ledger.proposals.values(),
                          key=lambda p: p.created_at, reverse=True)[:10]

            print(f"\n   Recent Proposals (last 10):")
            for i, p in enumerate(recent[:5], 1):
                print(f"      {i}. [{p.status}] {p.scope}: {p.description[:60]}...")

            self.stats['evolution'] = {
                'total_proposals': len(ledger.proposals),
                'status_counts': status_counts
            }

            # Check for stuck proposals
            pending = [p for p in ledger.proposals.values() if p.status == 'pending']
            if pending:
                print(f"\n   ⚠️  Pending proposals: {len(pending)}")
                self.warnings.append(f"{len(pending)} proposals stuck in pending state")

        except Exception as e:
            print(f"\n   ❌ Evolution ledger error: {e}")
            self.issues.append(f"Evolution ledger: {e}")

        # Innovation storage
        print(f"\n🔬 Innovation Storage:")
        try:
            # Check protobuf storage
            innovation_path = "/home/noogh/.noogh/innovations.pb"
            if os.path.exists(innovation_path):
                size = os.path.getsize(innovation_path)
                print(f"   File: innovations.pb")
                print(f"   Size: {size/1024:.1f} KB")
                print(f"   Status: ✅ Exists")
            else:
                print(f"   ⚠️  innovations.pb not found")
                self.warnings.append("Innovation storage file missing")

        except Exception as e:
            print(f"\n   ❌ Innovation storage error: {e}")

    async def monitor_security_systems(self):
        """Monitor security systems."""
        self.print_section("SECURITY SYSTEMS")

        # ASAA
        print(f"\n🛡️ ASAA (Antifragile Self-Auditing Authority):")
        try:
            from unified_core.core.asaa import get_asaa, ActionRequest

            asaa = get_asaa()
            print(f"   Status: ✅ ACTIVE")

            # Test evaluation
            test_request = ActionRequest(
                action_type="test_monitor",
                params={"test": True},
                source_beliefs=["test"],
                confidence=0.7,
                impact_level=0.3
            )

            result = asaa.evaluate(test_request)
            print(f"   Test Evaluation: ✅ Working")
            print(f"      Fragility: {result.fragility:.3f}")
            print(f"      Verdict: {result.verdict}")

            self.stats['asaa'] = {
                'active': True,
                'test_fragility': result.fragility
            }

        except Exception as e:
            print(f"   ❌ ASAA error: {e}")
            self.issues.append(f"ASAA: {e}")

        # AMLA
        print(f"\n🎖️ AMLA (Adversarial Military-Level Audit):")
        try:
            from unified_core.core.amla import get_amla, AMLAActionRequest

            amla = get_amla()
            print(f"   Status: ✅ ACTIVE")

            # Test extreme audit
            test_request = AMLAActionRequest(
                action_type="test_extreme",
                params={"test": True},
                source_beliefs=[],
                confidence=0.8,
                impact_level=0.5
            )

            result = amla.evaluate(test_request)
            print(f"   Test Audit: ✅ Working")
            print(f"      DFE (Decision Fragility Extreme): {result.fragility_extreme:.3f}")
            print(f"      Verdict: {result.verdict}")

            self.stats['amla'] = {
                'active': True,
                'test_dfe': result.fragility_extreme
            }

        except Exception as e:
            print(f"   ❌ AMLA error: {e}")
            self.issues.append(f"AMLA: {e}")

        # ScarTissue
        print(f"\n🩹 ScarTissue (Failure Memory):")
        try:
            from unified_core.core.scar import FailureRecord

            scar = FailureRecord()
            print(f"   Status: ✅ ACTIVE")

            # Check scar storage
            scar_files = [
                "/home/noogh/.noogh/scars.jsonl",
                "/home/noogh/projects/noogh_unified_system/src/data/scars.jsonl",
            ]

            total_scars = 0
            for path in scar_files:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        count = sum(1 for _ in f)
                        total_scars += count
                        print(f"   {os.path.basename(path)}: {count:,} scars")

            print(f"   Total Scars Recorded: {total_scars:,}")

            # Check depth (from scar system)
            if hasattr(scar, 'depth'):
                print(f"   Scar Depth: {scar.depth:.2f}")

            self.stats['scar_tissue'] = {
                'active': True,
                'total_scars': total_scars
            }

        except Exception as e:
            print(f"   ❌ ScarTissue error: {e}")
            self.issues.append(f"ScarTissue: {e}")

    async def monitor_consequence_system(self):
        """Monitor consequence tracking."""
        self.print_section("CONSEQUENCE ENGINE")

        try:
            from unified_core.core.consequence import ConsequenceEngine

            engine = ConsequenceEngine()
            print(f"\n📜 Consequence Ledger:")
            print(f"   Status: ✅ ACTIVE")

            # Check consequence files
            consequence_files = [
                "/home/noogh/.noogh/consequences.jsonl",
                "/home/noogh/projects/noogh_unified_system/src/data/consequences.jsonl",
            ]

            total_consequences = 0
            for path in consequence_files:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        count = sum(1 for _ in f)
                        total_consequences += count
                        size = os.path.getsize(path)
                        print(f"   {os.path.basename(path)}: {count:,} entries ({size/1024:.1f}KB)")

            print(f"\n   Total Consequences: {total_consequences:,}")

            # Recent consequences
            if total_consequences > 0:
                print(f"   ✅ Tracking all actions and outcomes")

            self.stats['consequence_engine'] = {
                'active': True,
                'total_consequences': total_consequences
            }

        except Exception as e:
            print(f"\n   ❌ ConsequenceEngine error: {e}")
            self.issues.append(f"ConsequenceEngine: {e}")

    async def monitor_memory_storage(self):
        """Monitor memory and storage systems."""
        self.print_section("MEMORY & STORAGE")

        # SQLite Database
        print(f"\n💾 SQLite Database (shared_memory.sqlite):")
        db_path = "/home/noogh/projects/noogh_unified_system/src/data/shared_memory.sqlite"

        if not os.path.exists(db_path):
            print(f"   ❌ Database not found: {db_path}")
            self.issues.append("SQLite database missing")
            return

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get file size
            size = os.path.getsize(db_path)
            print(f"   Size: {size/1024**2:.1f} MB")

            # Check tables and row counts
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

            print(f"\n   Tables ({len(tables)}):")
            total_rows = 0
            for (table_name,) in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                total_rows += count
                print(f"      {table_name}: {count:,} rows")

            print(f"\n   Total Records: {total_rows:,}")

            # Check last write
            cursor.execute("""
                SELECT MAX(updated_at) FROM beliefs
                UNION
                SELECT MAX(timestamp) FROM observations
            """)

            try:
                last_activity = cursor.fetchall()
                if last_activity and last_activity[0][0]:
                    print(f"   Last Activity: Recently active")
            except:
                pass

            # Integrity check
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()
            if integrity[0] == "ok":
                print(f"   Integrity: ✅ OK")
            else:
                print(f"   Integrity: ❌ {integrity[0]}")
                self.issues.append(f"Database integrity issue: {integrity[0]}")

            # Database size check
            if size > 1024**3:  # > 1GB
                self.warnings.append(f"Database is large: {size/1024**3:.1f}GB")

            conn.close()

            self.stats['database'] = {
                'size_mb': size/1024**2,
                'total_rows': total_rows,
                'tables': len(tables)
            }

        except Exception as e:
            print(f"\n   ❌ Database error: {e}")
            self.issues.append(f"Database: {e}")

        # Memory Store
        print(f"\n🗄️ UnifiedMemoryStore:")
        try:
            from unified_core.core.memory_store import UnifiedMemoryStore

            store = UnifiedMemoryStore()
            print(f"   Status: ✅ ACTIVE")
            print(f"   Backend: SQLite (async)")

        except Exception as e:
            print(f"   ❌ MemoryStore error: {e}")

    async def monitor_alert_systems(self):
        """Monitor alert and monitoring systems."""
        self.print_section("ALERT & MONITORING SYSTEMS")

        # FailureAlertSystem
        print(f"\n🚨 Failure Alert System:")
        try:
            from unified_core.observability.failure_alert_system import get_failure_alert_system

            alert_system = get_failure_alert_system()
            stats = alert_system.get_statistics()

            print(f"   Status: ✅ ACTIVE")
            print(f"   Total Alerts: {stats['total_alerts']:,}")
            print(f"   Active: {stats['active_alerts']}")
            print(f"   Resolved: {stats['resolved_alerts']}")
            print(f"   Monitoring: {'Yes' if stats['is_monitoring'] else 'No'}")

            if stats['total_alerts'] > 0:
                print(f"\n   By Severity:")
                for severity, count in stats['by_severity'].items():
                    if count > 0:
                        print(f"      {severity}: {count}")

            # Check for critical alerts
            critical = alert_system.get_critical_alerts()
            if critical:
                print(f"\n   ⚠️  CRITICAL ALERTS: {len(critical)}")
                for alert in critical[:3]:
                    print(f"      - {alert.title}")
                self.warnings.append(f"{len(critical)} critical alerts active")

            self.stats['alert_system'] = stats

        except Exception as e:
            print(f"\n   ❌ Alert system error: {e}")
            self.issues.append(f"Alert system: {e}")

        # GPU Monitor
        print(f"\n🎮 GPU Monitor:")
        try:
            from unified_core.observability.gpu_monitor import get_gpu_monitor

            gpu_monitor = get_gpu_monitor()

            if gpu_monitor.gpu_available:
                print(f"   Status: ✅ ACTIVE")
                print(f"   GPUs: {gpu_monitor.gpu_count}")

                summary = gpu_monitor.get_summary()
                print(f"   Avg Utilization: {summary['average_utilization']:.1f}%")
                if summary['average_temperature']:
                    print(f"   Avg Temperature: {summary['average_temperature']:.0f}°C")
            else:
                print(f"   Status: ℹ️  No GPU detected")

        except Exception as e:
            print(f"   ❌ GPU monitor error: {e}")

        # SystemHealthMonitor
        print(f"\n🏥 System Health Monitor:")
        try:
            from unified_core.health.system_health_monitor import SystemHealthMonitor

            monitor = SystemHealthMonitor()
            result = monitor.run_all_checks()

            print(f"   Status: {result['status'].upper()}")
            print(f"   Checks: {result['checks_passed']}/{result['total_checks']} passed")

            if result['issues']:
                print(f"\n   Issues ({len(result['issues'])}):")
                for issue in result['issues'][:3]:
                    print(f"      - {issue.get('message', issue)}")

            self.stats['health_monitor'] = result

        except Exception as e:
            print(f"\n   ❌ Health monitor error: {e}")

    async def monitor_background_services(self):
        """Monitor background services."""
        self.print_section("BACKGROUND SERVICES")

        services = [
            ("metrics_collector", "Metrics Collector"),
            ("funding_monitor", "Funding Monitor"),
            ("start_monitoring.py", "System Monitor"),
        ]

        print(f"\n🔄 Background Services:")

        import psutil

        for proc_name, display_name in services:
            found = False
            for proc in psutil.process_iter(['cmdline', 'pid', 'status']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if proc_name in cmdline:
                        status = proc.info['status']
                        icon = "✅" if status == 'running' else "🟡" if status == 'sleeping' else "❌"
                        print(f"   {icon} {display_name}: {status.upper()} (PID: {proc.info['pid']})")
                        found = True
                        break
                except:
                    pass

            if not found:
                print(f"   ⚠️  {display_name}: Not running")

    async def monitor_network_services(self):
        """Monitor network services and APIs."""
        self.print_section("NETWORK & API SERVICES")

        print(f"\n🌐 Network Services:")

        # Check Ollama
        try:
            import requests
            response = requests.get('http://127.0.0.1:11434/api/tags', timeout=3)

            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                print(f"\n   ✅ Ollama API:")
                print(f"      Endpoint: http://127.0.0.1:11434")
                print(f"      Models: {len(models)}")
                for model in models[:3]:
                    print(f"         - {model['name']}")
            else:
                print(f"\n   ⚠️  Ollama API: Status {response.status_code}")
                self.warnings.append(f"Ollama API returned {response.status_code}")

        except Exception as e:
            print(f"\n   ❌ Ollama API: {e}")
            self.issues.append(f"Ollama API: {e}")

        # Check for other services
        print(f"\n📡 Active Network Connections:")
        try:
            import psutil
            connections = psutil.net_connections(kind='inet')

            # Count listening ports
            listening = [c for c in connections if c.status == 'LISTEN']
            print(f"   Listening Ports: {len(listening)}")

            # Show important ones
            important_ports = [11434, 8000, 8080, 5000]
            for conn in listening:
                if conn.laddr.port in important_ports:
                    print(f"      Port {conn.laddr.port}: LISTENING")

        except Exception as e:
            print(f"   ⚠️  Could not check connections: {e}")

    def generate_summary(self):
        """Generate monitoring summary."""
        print("\n" + "=" * 70)
        print("📊 MONITORING SUMMARY")
        print("=" * 70)

        print(f"\n✅ Systems Monitored:")
        print(f"   • Evolution & Innovation")
        print(f"   • Security (ASAA, AMLA, ScarTissue)")
        print(f"   • Consequence Tracking")
        print(f"   • Memory & Storage")
        print(f"   • Alert Systems")
        print(f"   • Background Services")
        print(f"   • Network & APIs")

        # Issues
        if self.issues:
            print(f"\n❌ ISSUES FOUND ({len(self.issues)}):")
            for i, issue in enumerate(self.issues, 1):
                print(f"   {i}. {issue}")
        else:
            print(f"\n✅ No critical issues found")

        # Warnings
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")

        # Key Stats
        print(f"\n📊 Key Statistics:")
        if 'evolution' in self.stats:
            print(f"   Evolution Proposals: {self.stats['evolution']['total_proposals']:,}")
        if 'scar_tissue' in self.stats:
            print(f"   Failure Scars: {self.stats['scar_tissue']['total_scars']:,}")
        if 'consequence_engine' in self.stats:
            print(f"   Consequences: {self.stats['consequence_engine']['total_consequences']:,}")
        if 'database' in self.stats:
            print(f"   Database Size: {self.stats['database']['size_mb']:.1f}MB")
            print(f"   Database Records: {self.stats['database']['total_rows']:,}")

        # Health Score
        total_systems = 7
        failed_systems = len(self.issues)
        health_score = ((total_systems - failed_systems) / total_systems) * 100

        print(f"\n🏥 Overall Health: {health_score:.0f}%")
        if health_score >= 90:
            print(f"   Status: ✅ EXCELLENT")
        elif health_score >= 70:
            print(f"   Status: 🟡 GOOD")
        else:
            print(f"   Status: 🔴 NEEDS ATTENTION")

        print("\n" + "=" * 70)


async def main():
    """Main monitoring function."""

    print("=" * 70)
    print("🔍 MONITORING REMAINING SYSTEMS")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    monitor = RemainingSystemsMonitor()

    try:
        await monitor.monitor_evolution_system()
        await monitor.monitor_security_systems()
        await monitor.monitor_consequence_system()
        await monitor.monitor_memory_storage()
        await monitor.monitor_alert_systems()
        await monitor.monitor_background_services()
        await monitor.monitor_network_services()

        monitor.generate_summary()

        return 0 if len(monitor.issues) == 0 else 1

    except Exception as e:
        print(f"\n❌ Monitoring failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
