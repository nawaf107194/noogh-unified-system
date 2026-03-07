"""
Comprehensive System Monitor - مراقب النظام الشامل
==================================================

Monitors all NOOGH subsystems:
- Development & Evolution
- Learning & Intelligence
- Trading
- GPU & Resources
- Health & Alerts
"""

import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime


def print_header(title):
    """Print section header."""
    print("\n" + "=" * 60)
    print(f"📊 {title}")
    print("=" * 60)


async def monitor_development_system():
    """Monitor development and evolution systems."""

    print_header("Development & Evolution System")

    results = {
        "evolution_ledger": {},
        "innovations": {},
        "proposals": {}
    }

    # 1. Evolution Ledger
    print("\n1️⃣ Evolution Ledger:")
    try:
        from unified_core.evolution.ledger import EvolutionLedger

        ledger = EvolutionLedger()

        stats = {
            "total_proposals": len(ledger.proposals),
            "pending": sum(1 for p in ledger.proposals.values() if p.status == "pending"),
            "promoted": sum(1 for p in ledger.proposals.values() if p.status == "promoted"),
            "failed": sum(1 for p in ledger.proposals.values() if p.status == "failed"),
            "rejected": sum(1 for p in ledger.proposals.values() if p.status == "rejected"),
        }

        results["evolution_ledger"] = stats

        print(f"   Total Proposals: {stats['total_proposals']}")
        print(f"   ├─ Pending: {stats['pending']}")
        print(f"   ├─ Promoted: {stats['promoted']}")
        print(f"   ├─ Failed: {stats['failed']}")
        print(f"   └─ Rejected: {stats['rejected']}")

        if stats['promoted'] > 0:
            success_rate = (stats['promoted'] / stats['total_proposals'] * 100)
            print(f"   Success Rate: {success_rate:.1f}%")

    except Exception as e:
        print(f"   ⚠️  Evolution Ledger: {e}")

    # 2. Innovation Storage
    print("\n2️⃣ Innovation Storage:")
    try:
        from unified_core.storage.protobuf import get_innovation_storage

        storage = get_innovation_storage()
        innovations = storage.load_all()

        results["innovations"] = {
            "total": len(innovations),
            "by_status": {}
        }

        print(f"   Total Innovations: {len(innovations)}")

        if innovations:
            # Group by status
            status_counts = {}
            for inn in innovations:
                status = inn.status
                status_counts[status] = status_counts.get(status, 0) + 1

            for status, count in status_counts.items():
                print(f"   ├─ {status}: {count}")
                results["innovations"]["by_status"][status] = count

    except Exception as e:
        print(f"   ⚠️  Innovation Storage: {e}")

    return results


async def monitor_learning_system():
    """Monitor learning and intelligence systems."""

    print_header("Learning & Intelligence System")

    results = {
        "neuron_fabric": {},
        "world_model": {},
        "beliefs": {}
    }

    # 1. NeuronFabric
    print("\n1️⃣ NeuronFabric:")
    try:
        from unified_core.core.neuron_fabric import get_neuron_fabric

        fabric = get_neuron_fabric()

        total_neurons = len(fabric._neurons)
        total_synapses = len(fabric._synapses)

        # Count by domain
        domains = {}
        for neuron in fabric._neurons.values():
            domains[neuron.domain] = domains.get(neuron.domain, 0) + 1

        results["neuron_fabric"] = {
            "total_neurons": total_neurons,
            "total_synapses": total_synapses,
            "by_domain": domains
        }

        print(f"   Total Neurons: {total_neurons:,}")
        print(f"   Total Synapses: {total_synapses:,}")
        print(f"   Average Connections: {total_synapses/total_neurons:.1f}" if total_neurons > 0 else "   No neurons")

        print(f"\n   By Domain:")
        for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"      {domain}: {count:,}")

    except Exception as e:
        print(f"   ⚠️  NeuronFabric: {e}")

    # 2. WorldModel
    print("\n2️⃣ WorldModel:")
    try:
        from unified_core.core.world_model import WorldModel

        wm = WorldModel()
        await wm.setup()

        belief_state = await wm.get_belief_state()

        results["world_model"] = belief_state

        print(f"   Total Beliefs: {belief_state['total_beliefs']:,}")
        print(f"   ├─ Active: {belief_state['active']:,}")
        print(f"   ├─ Weakened: {belief_state['weakened']:,}")
        print(f"   └─ Falsified: {belief_state['falsified']:,}")
        print(f"   Avg Confidence: {belief_state['average_confidence']:.3f}")
        print(f"   Total Falsifications: {belief_state['total_falsifications']:,}")

        # Trading beliefs
        beliefs = await wm.get_usable_beliefs()
        trading_beliefs = [b for b in beliefs if any(kw in b.proposition.lower()
                          for kw in ['trade', 'market', 'btc', 'price'])]

        results["beliefs"]["trading"] = len(trading_beliefs)
        print(f"   Trading Beliefs: {len(trading_beliefs):,}")

    except Exception as e:
        print(f"   ⚠️  WorldModel: {e}")

    # 3. ASAA & AMLA
    print("\n3️⃣ Decision Auditing:")
    try:
        from unified_core.core.asaa import get_asaa
        from unified_core.core.amla import get_amla

        asaa = get_asaa()
        amla = get_amla()

        print(f"   ✅ ASAA: Active (Antifragile auditing)")
        print(f"   ✅ AMLA: Active (Military-level auditing)")

    except Exception as e:
        print(f"   ⚠️  Decision Auditing: {e}")

    return results


async def monitor_trading_system():
    """Monitor trading system."""

    print_header("Trading System")

    results = {
        "trap_trader": {},
        "market_beliefs": {},
        "alerts": {}
    }

    # 1. TrapLiveTrader Status
    print("\n1️⃣ TrapLiveTrader:")
    try:
        from trading.trap_live_trader import TrapLiveTrader

        print(f"   ✅ TrapLiveTrader module available")
        print(f"   Integration: EventBus, NeuronFabric, AMLA, ConsequenceEngine")

        # Check if running
        import subprocess
        result = subprocess.run(
            ['pgrep', '-f', 'trap_live_trader'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            print(f"   ✅ Running (PID: {pids[0]})")
            results["trap_trader"]["running"] = True
        else:
            print(f"   ⚠️  Not currently running")
            results["trap_trader"]["running"] = False

    except Exception as e:
        print(f"   ⚠️  TrapLiveTrader: {e}")

    # 2. Market Belief Engine
    print("\n2️⃣ Market Belief Engine:")
    try:
        from trading.market_belief_engine import get_market_belief_engine

        engine = get_market_belief_engine()

        print(f"   ✅ MarketBeliefEngine ready")
        print(f"   Converts market data → WorldModel beliefs")

    except Exception as e:
        print(f"   ⚠️  MarketBeliefEngine: {e}")

    # 3. ConsequenceEngine (Trading)
    print("\n3️⃣ Trading Consequences:")
    try:
        from unified_core.core.consequence import ConsequenceEngine

        engine = ConsequenceEngine(storage_name="trading_consequences.jsonl")

        total = len(engine.consequences)
        print(f"   Total Recorded: {total:,}")

        if total > 0:
            recent = sorted(engine.consequences.values(),
                          key=lambda c: c.timestamp, reverse=True)[:5]
            print(f"   Recent consequences:")
            for c in recent[:3]:
                timestamp = datetime.fromtimestamp(c.timestamp).strftime("%Y-%m-%d %H:%M")
                print(f"      {timestamp}: {c.action.action_type}")

    except Exception as e:
        print(f"   ⚠️  ConsequenceEngine: {e}")

    # 4. ScarTissue (Trading Failures)
    print("\n4️⃣ Trading Scars:")
    try:
        from unified_core.core.scar import FailureRecord

        scar = FailureRecord()

        total_scars = len(scar.scars)
        print(f"   Total Scars: {total_scars:,}")

        if total_scars > 0:
            # Count trading-related scars
            trading_scars = [s for s in scar.scars.values()
                           if 'trade' in s.action_type.lower() or 'trading' in s.action_type.lower()]
            print(f"   Trading Scars: {len(trading_scars)}")

    except Exception as e:
        print(f"   ⚠️  ScarTissue: {e}")

    return results


async def monitor_resources_gpu():
    """Monitor system resources and GPU."""

    print_header("Resources & GPU")

    results = {
        "cpu": 0,
        "memory": 0,
        "disk": 0,
        "gpu": {}
    }

    # 1. System Resources
    print("\n1️⃣ System Resources:")
    try:
        import psutil

        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        results["cpu"] = cpu
        results["memory"] = memory.percent
        results["disk"] = disk.percent

        print(f"   CPU: {cpu:.1f}%")
        print(f"   Memory: {memory.percent:.1f}% ({memory.used/1024**3:.1f}GB / {memory.total/1024**3:.1f}GB)")
        print(f"   Disk: {disk.percent:.1f}% ({disk.used/1024**3:.1f}GB / {disk.total/1024**3:.1f}GB)")

        # Status indicators
        if cpu > 80:
            print(f"   ⚠️  High CPU usage")
        if memory.percent > 80:
            print(f"   ⚠️  High memory usage")
        if disk.percent > 80:
            print(f"   ⚠️  Low disk space")

    except Exception as e:
        print(f"   ⚠️  Resource monitoring: {e}")

    # 2. GPU
    print("\n2️⃣ GPU Status:")
    try:
        from unified_core.observability.gpu_monitor import get_gpu_monitor

        gpu_monitor = get_gpu_monitor()

        if gpu_monitor.gpu_available:
            metrics = gpu_monitor.get_metrics()

            for metric in metrics:
                results["gpu"][f"gpu_{metric.index}"] = {
                    "name": metric.name,
                    "memory_used_percent": metric.memory_used_percent,
                    "utilization": metric.utilization_percent,
                    "temperature": metric.temperature_celsius
                }

                print(f"   GPU {metric.index}: {metric.name}")
                print(f"      Memory: {metric.memory_used_percent:.1f}%")
                print(f"      Utilization: {metric.utilization_percent:.1f}%")
                if metric.temperature_celsius:
                    print(f"      Temperature: {metric.temperature_celsius:.1f}°C")
        else:
            print(f"   ℹ️  No GPU detected")

    except Exception as e:
        print(f"   ⚠️  GPU monitoring: {e}")

    return results


async def monitor_health_alerts():
    """Monitor health and alerts."""

    print_header("Health & Alerts")

    results = {
        "health": {},
        "alerts": {}
    }

    # 1. System Health
    print("\n1️⃣ System Health:")
    try:
        from unified_core.health.system_health_monitor import SystemHealthMonitor

        monitor = SystemHealthMonitor()
        result = monitor.run_all_checks()

        results["health"] = result

        print(f"   Status: {result['status'].upper()}")
        print(f"   Checks: {result['checks_passed']}/{result['total_checks']} passed")

        if result['issues']:
            print(f"   Issues: {len(result['issues'])}")
            for issue in result['issues'][:3]:
                print(f"      - {issue}")

    except Exception as e:
        print(f"   ⚠️  System Health: {e}")

    # 2. Failure Alert System
    print("\n2️⃣ Failure Alerts:")
    try:
        from unified_core.observability.failure_alert_system import get_failure_alert_system

        alert_system = get_failure_alert_system()
        stats = alert_system.get_statistics()

        results["alerts"] = stats

        print(f"   Total Alerts: {stats['total_alerts']}")
        print(f"   Active: {stats['active_alerts']}")
        print(f"   Resolved: {stats['resolved_alerts']}")

        if stats['total_alerts'] > 0:
            print(f"\n   By Severity:")
            for severity, count in stats['by_severity'].items():
                if count > 0:
                    print(f"      {severity}: {count}")

        # Check critical alerts
        critical = alert_system.get_critical_alerts()
        if critical:
            print(f"\n   ⚠️  {len(critical)} CRITICAL alerts active!")
            for alert in critical[:3]:
                print(f"      - {alert.title}")

    except Exception as e:
        print(f"   ⚠️  Failure Alerts: {e}")

    # 3. EventBus
    print("\n3️⃣ EventBus:")
    try:
        from unified_core.integration.event_bus import get_event_bus

        bus = get_event_bus()

        print(f"   ✅ EventBus active")
        print(f"   Subscribers: {len(bus._subscribers)}")

    except Exception as e:
        print(f"   ⚠️  EventBus: {e}")

    return results


async def monitor_agents():
    """Monitor autonomous agents."""

    print_header("Autonomous Agents")

    results = {}

    print("\n1️⃣ Agent Processes:")

    agent_processes = [
        ("agent_daemon", "Agent Daemon"),
        ("autonomous_trading", "Trading Agent"),
        ("noogh_orchestrator", "Orchestrator"),
    ]

    for proc_name, display_name in agent_processes:
        try:
            import subprocess
            result = subprocess.run(
                ['pgrep', '-f', proc_name],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                print(f"   ✅ {display_name}: Running (PID: {pids[0]})")
                results[proc_name] = True
            else:
                print(f"   ⚠️  {display_name}: Not running")
                results[proc_name] = False
        except Exception as e:
            print(f"   ⚠️  {display_name}: {e}")

    return results


async def main():
    """Main monitoring function."""

    print("\n" + "=" * 60)
    print("🔍 NOOGH Comprehensive System Monitor")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    all_results = {}

    try:
        # Monitor all systems
        all_results["development"] = await monitor_development_system()
        all_results["learning"] = await monitor_learning_system()
        all_results["trading"] = await monitor_trading_system()
        all_results["resources"] = await monitor_resources_gpu()
        all_results["health"] = await monitor_health_alerts()
        all_results["agents"] = await monitor_agents()

        # Final Summary
        print_header("System Summary")

        print("\n✅ Systems Monitored:")
        print("   ✓ Development & Evolution")
        print("   ✓ Learning & Intelligence")
        print("   ✓ Trading")
        print("   ✓ Resources & GPU")
        print("   ✓ Health & Alerts")
        print("   ✓ Autonomous Agents")

        print("\n📊 Key Metrics:")

        # Learning
        if "learning" in all_results and "neuron_fabric" in all_results["learning"]:
            nf = all_results["learning"]["neuron_fabric"]
            print(f"   Neurons: {nf.get('total_neurons', 0):,}")

        # Beliefs
        if "learning" in all_results and "world_model" in all_results["learning"]:
            wm = all_results["learning"]["world_model"]
            print(f"   Beliefs: {wm.get('total_beliefs', 0):,}")

        # Resources
        if "resources" in all_results:
            res = all_results["resources"]
            print(f"   CPU: {res.get('cpu', 0):.1f}%")
            print(f"   Memory: {res.get('memory', 0):.1f}%")

        # Alerts
        if "health" in all_results and "alerts" in all_results["health"]:
            alerts = all_results["health"]["alerts"]
            print(f"   Active Alerts: {alerts.get('active_alerts', 0)}")

        print("\n" + "=" * 60)
        print("✅ Monitoring Complete")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Monitoring failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
