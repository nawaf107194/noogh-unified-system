"""
Real-Time Deep Monitor - مراقب عميق في الوقت الفعلي
===================================================

Advanced real-time monitoring with:
- Live process tracking
- Performance analysis
- Log streaming
- Resource trends
- Anomaly detection
"""

import asyncio
import sys
import os
import time
import psutil
from datetime import datetime
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class RealtimeMonitor:
    """Real-time system monitor."""

    def __init__(self, duration=30):
        self.duration = duration
        self.start_time = time.time()
        self.metrics_history = {
            'cpu': deque(maxlen=60),
            'memory': deque(maxlen=60),
            'gpu_memory': deque(maxlen=60),
            'gpu_temp': deque(maxlen=60),
        }
        self.anomalies = []
        self.errors_found = []

    def print_header(self):
        """Print monitor header."""
        print("\n" + "=" * 70)
        print("🔴 LIVE DEEP MONITORING - مراقبة عميقة مباشرة")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Duration: {self.duration} seconds")
        print("=" * 70)

    async def check_process_details(self):
        """Detailed process analysis."""
        print("\n" + "─" * 70)
        print("🔍 PROCESS ANALYSIS")
        print("─" * 70)

        critical_processes = {
            'agent_daemon': [],
            'ollama': [],
            'trading_agent': [],
            'orchestrator': [],
        }

        # Find all Python/Ollama processes
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent', 'status']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])

                for key in critical_processes.keys():
                    if key in cmdline.lower():
                        critical_processes[key].append({
                            'pid': proc.info['pid'],
                            'cpu': proc.info['cpu_percent'],
                            'memory': proc.info['memory_percent'],
                            'status': proc.info['status'],
                            'cmdline': cmdline[:80]
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Display results
        for proc_name, procs in critical_processes.items():
            if procs:
                print(f"\n✓ {proc_name.upper()}: {len(procs)} process(es)")
                for p in procs[:3]:  # Show max 3
                    status_icon = "🟢" if p['status'] == 'running' else "🟡" if p['status'] == 'sleeping' else "🔴"
                    print(f"  {status_icon} PID {p['pid']}: CPU={p['cpu']:.1f}% MEM={p['memory']:.1f}% [{p['status']}]")

                    # Anomaly detection
                    if p['cpu'] > 50:
                        self.anomalies.append(f"High CPU in {proc_name} PID {p['pid']}: {p['cpu']:.1f}%")
                    if p['memory'] > 15:
                        self.anomalies.append(f"High memory in {proc_name} PID {p['pid']}: {p['memory']:.1f}%")
            else:
                print(f"\n⚠️  {proc_name.upper()}: NOT RUNNING")
                self.errors_found.append(f"{proc_name} is not running")

    async def monitor_resources_live(self):
        """Live resource monitoring."""
        print("\n" + "─" * 70)
        print("📊 RESOURCE MONITORING (Live)")
        print("─" * 70)

        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)
        self.metrics_history['cpu'].append(cpu_percent)

        print(f"\n💻 CPU:")
        print(f"   Overall: {cpu_percent:.1f}%")
        print(f"   Cores: {', '.join([f'{c:.0f}%' for c in cpu_per_core[:8]])}")

        if cpu_percent > 80:
            self.anomalies.append(f"High CPU usage: {cpu_percent:.1f}%")

        # Memory
        mem = psutil.virtual_memory()
        self.metrics_history['memory'].append(mem.percent)

        print(f"\n💾 Memory:")
        print(f"   Used: {mem.used/1024**3:.1f}GB / {mem.total/1024**3:.1f}GB ({mem.percent:.1f}%)")
        print(f"   Available: {mem.available/1024**3:.1f}GB")
        print(f"   Cached: {mem.cached/1024**3:.1f}GB" if hasattr(mem, 'cached') else "")

        if mem.percent > 85:
            self.anomalies.append(f"High memory usage: {mem.percent:.1f}%")

        # Disk
        disk = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()

        print(f"\n💿 Disk:")
        print(f"   Used: {disk.used/1024**3:.1f}GB / {disk.total/1024**3:.1f}GB ({disk.percent:.1f}%)")
        print(f"   I/O: Read={disk_io.read_bytes/1024**3:.1f}GB, Write={disk_io.write_bytes/1024**3:.1f}GB")

        # GPU
        try:
            from unified_core.observability.gpu_monitor import get_gpu_monitor

            gpu_monitor = get_gpu_monitor()
            if gpu_monitor.gpu_available:
                metrics = gpu_monitor.get_metrics()

                for metric in metrics:
                    self.metrics_history['gpu_memory'].append(metric.memory_used_percent)
                    if metric.temperature_celsius:
                        self.metrics_history['gpu_temp'].append(metric.temperature_celsius)

                    print(f"\n🎮 GPU {metric.index}: {metric.name}")
                    print(f"   Memory: {metric.memory_used_mb:.0f}MB / {metric.memory_total_mb:.0f}MB ({metric.memory_used_percent:.1f}%)")
                    print(f"   Utilization: {metric.utilization_percent:.1f}%")
                    if metric.temperature_celsius:
                        print(f"   Temperature: {metric.temperature_celsius:.0f}°C")
                    if metric.power_draw_watts:
                        print(f"   Power: {metric.power_draw_watts:.0f}W / {metric.power_limit_watts:.0f}W")

                    # Anomaly detection
                    if metric.memory_used_percent > 95:
                        self.anomalies.append(f"GPU {metric.index} memory critical: {metric.memory_used_percent:.1f}%")
                    if metric.temperature_celsius and metric.temperature_celsius > 85:
                        self.anomalies.append(f"GPU {metric.index} overheating: {metric.temperature_celsius:.0f}°C")
        except Exception as e:
            print(f"\n⚠️  GPU monitoring: {e}")

    async def analyze_log_activity(self):
        """Analyze recent log activity."""
        print("\n" + "─" * 70)
        print("📝 RECENT LOG ACTIVITY")
        print("─" * 70)

        log_files = [
            "/home/noogh/projects/noogh_unified_system/logs/agent_daemon.log",
            "/home/noogh/projects/noogh_unified_system/logs/trading_signals.log",
            "/home/noogh/.noogh/logs/system.log",
        ]

        for log_path in log_files:
            if os.path.exists(log_path):
                try:
                    # Get file size and last modified
                    stat = os.stat(log_path)
                    size_mb = stat.st_size / 1024**2
                    modified = datetime.fromtimestamp(stat.st_mtime)

                    print(f"\n📄 {os.path.basename(log_path)}:")
                    print(f"   Size: {size_mb:.1f}MB")
                    print(f"   Modified: {modified.strftime('%Y-%m-%d %H:%M:%S')}")

                    # Read last 50 lines
                    with open(log_path, 'r') as f:
                        lines = f.readlines()[-50:]

                        # Count errors/warnings
                        errors = [l for l in lines if 'ERROR' in l.upper() or 'EXCEPTION' in l.upper()]
                        warnings = [l for l in lines if 'WARNING' in l.upper() or 'WARN' in l.upper()]

                        print(f"   Recent (last 50 lines): {len(errors)} errors, {len(warnings)} warnings")

                        if errors:
                            print(f"   Latest error: {errors[-1].strip()[:80]}...")
                            self.errors_found.append(f"Error in {os.path.basename(log_path)}")

                except Exception as e:
                    print(f"   ⚠️  Could not read: {e}")

    async def check_neural_activity(self):
        """Check neural/cognitive activity."""
        print("\n" + "─" * 70)
        print("🧠 NEURAL ACTIVITY")
        print("─" * 70)

        try:
            from unified_core.core.neuron_fabric import get_neuron_fabric
            from unified_core.core.world_model import WorldModel

            # NeuronFabric
            fabric = get_neuron_fabric()
            total_neurons = len(fabric._neurons)
            total_synapses = len(fabric._synapses)

            print(f"\n🔷 NeuronFabric:")
            print(f"   Neurons: {total_neurons:,}")
            print(f"   Synapses: {total_synapses:,}")
            print(f"   Avg Connections: {total_synapses/total_neurons:.1f}" if total_neurons > 0 else "")

            # Recent neuron activity (check energy levels)
            active_neurons = [n for n in fabric._neurons.values() if n.energy > 0.5]
            print(f"   Active (energy>0.5): {len(active_neurons):,}")

            # WorldModel
            wm = WorldModel()
            await wm.setup()

            belief_state = await wm.get_belief_state()

            print(f"\n🔷 WorldModel:")
            print(f"   Total Beliefs: {belief_state['total_beliefs']:,}")
            print(f"   Active: {belief_state['active']:,}")
            print(f"   Avg Confidence: {belief_state['average_confidence']:.3f}")
            print(f"   Falsifications: {belief_state['total_falsifications']:,}")

        except Exception as e:
            print(f"\n⚠️  Neural analysis: {e}")
            self.errors_found.append(f"Neural analysis failed: {e}")

    async def check_trading_activity(self):
        """Check trading system activity."""
        print("\n" + "─" * 70)
        print("💹 TRADING ACTIVITY")
        print("─" * 70)

        try:
            # Check if trading agent is running
            trading_running = False
            for proc in psutil.process_iter(['cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'autonomous_trading_agent' in cmdline or 'trap_live_trader' in cmdline:
                        trading_running = True
                        break
                except:
                    pass

            if trading_running:
                print(f"\n✓ Trading Agent: ACTIVE")
            else:
                print(f"\n⚠️  Trading Agent: INACTIVE")

            # Check recent trading beliefs
            from unified_core.core.world_model import WorldModel
            wm = WorldModel()
            await wm.setup()

            beliefs = await wm.get_usable_beliefs()
            trading_beliefs = [b for b in beliefs if any(kw in b.proposition.lower()
                              for kw in ['trade', 'market', 'btc', 'price', 'signal'])]

            print(f"\n🔷 Trading Beliefs: {len(trading_beliefs):,}")

            if trading_beliefs:
                # Show most recent
                recent = sorted(trading_beliefs, key=lambda b: b.created_at, reverse=True)[:3]
                print(f"\n   Recent beliefs:")
                for b in recent:
                    print(f"   • {b.proposition[:60]}... (conf: {b.confidence:.2f})")

        except Exception as e:
            print(f"\n⚠️  Trading analysis: {e}")

    async def check_event_bus_activity(self):
        """Check EventBus activity."""
        print("\n" + "─" * 70)
        print("📡 EVENTBUS ACTIVITY")
        print("─" * 70)

        try:
            from unified_core.integration.event_bus import get_event_bus, StandardEvents

            bus = get_event_bus()

            print(f"\n✓ EventBus: ACTIVE")

            # Test pub/sub
            test_events = []

            async def test_handler(event):
                test_events.append(event)

            bus.subscribe(StandardEvents.BELIEF_ADDED, test_handler, "monitor_test")

            await bus.publish(StandardEvents.BELIEF_ADDED, {"test": "monitor"}, "monitor")
            await asyncio.sleep(0.1)

            bus.unsubscribe(StandardEvents.BELIEF_ADDED, "monitor_test")

            if test_events:
                print(f"   Pub/Sub: ✓ Working (latency <100ms)")
            else:
                print(f"   Pub/Sub: ⚠️  No events received")
                self.errors_found.append("EventBus pub/sub not responding")

        except Exception as e:
            print(f"\n⚠️  EventBus check: {e}")
            self.errors_found.append(f"EventBus error: {e}")

    async def display_trends(self):
        """Display resource trends."""
        print("\n" + "─" * 70)
        print("📈 RESOURCE TRENDS")
        print("─" * 70)

        if len(self.metrics_history['cpu']) > 1:
            cpu_avg = sum(self.metrics_history['cpu']) / len(self.metrics_history['cpu'])
            cpu_max = max(self.metrics_history['cpu'])

            print(f"\n💻 CPU (last {len(self.metrics_history['cpu'])}s):")
            print(f"   Average: {cpu_avg:.1f}%")
            print(f"   Peak: {cpu_max:.1f}%")
            print(f"   Trend: {'📈 Rising' if cpu_avg > 5 else '📉 Low'}")

        if len(self.metrics_history['memory']) > 1:
            mem_avg = sum(self.metrics_history['memory']) / len(self.metrics_history['memory'])

            print(f"\n💾 Memory:")
            print(f"   Average: {mem_avg:.1f}%")
            print(f"   Stable: {'✓' if max(self.metrics_history['memory']) - min(self.metrics_history['memory']) < 5 else '⚠️  Fluctuating'}")

        if len(self.metrics_history['gpu_temp']) > 1:
            gpu_temp_avg = sum(self.metrics_history['gpu_temp']) / len(self.metrics_history['gpu_temp'])

            print(f"\n🎮 GPU Temperature:")
            print(f"   Average: {gpu_temp_avg:.0f}°C")
            print(f"   Status: {'✓ Cool' if gpu_temp_avg < 70 else '⚠️  Warm' if gpu_temp_avg < 80 else '🔴 Hot'}")

    def display_summary(self):
        """Display monitoring summary."""
        print("\n" + "=" * 70)
        print("📊 MONITORING SUMMARY")
        print("=" * 70)

        elapsed = time.time() - self.start_time

        print(f"\n⏱️  Duration: {elapsed:.1f}s")
        print(f"🔍 Checks Performed: Multiple categories")

        # Anomalies
        if self.anomalies:
            print(f"\n⚠️  ANOMALIES DETECTED ({len(self.anomalies)}):")
            for i, anomaly in enumerate(self.anomalies[:10], 1):
                print(f"   {i}. {anomaly}")
        else:
            print(f"\n✅ No anomalies detected")

        # Errors
        if self.errors_found:
            print(f"\n❌ ERRORS FOUND ({len(self.errors_found)}):")
            for i, error in enumerate(self.errors_found[:10], 1):
                print(f"   {i}. {error}")
        else:
            print(f"\n✅ No errors found")

        # Health Score
        total_checks = 10
        passed = total_checks - len(self.errors_found)
        health_score = (passed / total_checks) * 100

        print(f"\n🏥 System Health: {health_score:.0f}%")

        if health_score >= 90:
            print(f"   Status: ✅ EXCELLENT")
        elif health_score >= 70:
            print(f"   Status: 🟡 GOOD")
        else:
            print(f"   Status: 🔴 NEEDS ATTENTION")

        print("\n" + "=" * 70)


async def main():
    """Main monitoring loop."""

    monitor = RealtimeMonitor(duration=30)
    monitor.print_header()

    try:
        # Initial checks
        await monitor.check_process_details()
        await monitor.monitor_resources_live()
        await monitor.analyze_log_activity()
        await monitor.check_neural_activity()
        await monitor.check_trading_activity()
        await monitor.check_event_bus_activity()

        # Continuous monitoring for remaining duration
        print("\n" + "─" * 70)
        print("⏳ Continuous Monitoring... (tracking resource trends)")
        print("─" * 70)

        remaining = monitor.duration - (time.time() - monitor.start_time)

        while remaining > 0:
            # Update metrics
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory()

            monitor.metrics_history['cpu'].append(cpu)
            monitor.metrics_history['memory'].append(mem.percent)

            # Check GPU
            try:
                from unified_core.observability.gpu_monitor import get_gpu_monitor
                gpu_monitor = get_gpu_monitor()
                if gpu_monitor.gpu_available:
                    metrics = gpu_monitor.get_metrics()
                    for m in metrics:
                        monitor.metrics_history['gpu_memory'].append(m.memory_used_percent)
                        if m.temperature_celsius:
                            monitor.metrics_history['gpu_temp'].append(m.temperature_celsius)
            except:
                pass

            print(f"   [{int(remaining)}s] CPU: {cpu:.1f}% | MEM: {mem.percent:.1f}%", end='\r')

            await asyncio.sleep(2)
            remaining = monitor.duration - (time.time() - monitor.start_time)

        print()  # New line after progress

        # Final analysis
        await monitor.display_trends()
        monitor.display_summary()

        return 0 if len(monitor.errors_found) == 0 else 1

    except KeyboardInterrupt:
        print("\n\n⚠️  Monitoring interrupted by user")
        monitor.display_summary()
        return 1
    except Exception as e:
        print(f"\n❌ Monitoring error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
