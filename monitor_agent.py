#!/usr/bin/env python3
"""
Real-time Noogh Agent Monitoring Dashboard
مراقبة الوكيل في الوقت الفعلي
"""

import asyncio
import os
import sys
from datetime import datetime
from unified_core.agent_tracking import (
    get_agent_status,
    get_agent_health,
    get_agent_metrics,
    get_recent_decisions
)


def clear_screen():
    """Clear terminal screen"""
    os.system('clear' if os.name != 'nt' else 'cls')


def print_header():
    """Print dashboard header"""
    print("=" * 80)
    print("🤖 NOOGH AGENT MONITORING DASHBOARD | لوحة مراقبة وكيل نوغ".center(80))
    print("=" * 80)
    print(f"⏰ Time | الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


def print_status_section(status):
    """Print agent status section"""
    print("\n📊 AGENT STATUS | حالة الوكيل")
    print("-" * 80)
    
    # Status indicator
    status_emoji = "🟢" if status.status == "running" else "🔴"
    print(f"{status_emoji} Status: {status.status} | {status.arabic_status}")
    
    if status.pid:
        print(f"   PID: {status.pid}")
        print(f"   Uptime: {status.uptime_seconds:.0f}s ({status.uptime_seconds/60:.1f} minutes)")
        print(f"   CPU Usage: {status.cpu_percent:.1f}%")
        print(f"   Memory: {status.memory_mb:.1f} MB ({status.memory_percent:.1f}%)")
        print(f"   Threads: {status.num_threads}")
    
    if status.last_cycle_id:
        print(f"   Last Cycle: {status.last_cycle_id}")
        print(f"   Last Activity: {status.last_activity}")


def print_health_section(health):
    """Print agent health section"""
    print("\n💚 AGENT HEALTH | صحة الوكيل")
    print("-" * 80)
    
    health_emoji = {
        "healthy": "🟢",
        "degraded": "🟡",
        "stopped": "🔴",
        "unknown": "⚪"
    }.get(health.overall_health, "⚪")
    
    print(f"{health_emoji} Overall: {health.overall_health} | {health.arabic_health}")
    
    if health.components:
        print("   Components:")
        for component, status in health.components.items():
            comp_emoji = "✅" if status == "running" else "❌"
            print(f"      {comp_emoji} {component}: {status}")
    
    if health.warnings:
        print("   ⚠️  Warnings:")
        for warning in health.warnings:
            print(f"      • {warning}")


def print_metrics_section(metrics):
    """Print system metrics section"""
    print("\n📈 SYSTEM METRICS | مقاييس النظام")
    print("-" * 80)
    
    sys_metrics = metrics.get('system', {})
    print(f"   CPU: {sys_metrics.get('cpu_percent', 0):.1f}%")
    print(f"   Memory: {sys_metrics.get('memory_percent', 0):.1f}% "
          f"({sys_metrics.get('memory_used_gb', 0):.1f}GB / "
          f"{sys_metrics.get('memory_total_gb', 0):.1f}GB)")
    print(f"   Disk: {sys_metrics.get('disk_percent', 0):.1f}%")
    
    if 'agent' in metrics:
        agent_metrics = metrics['agent']
        print(f"\n   Agent Process:")
        print(f"      CPU: {agent_metrics.get('cpu_percent', 0):.1f}%")
        print(f"      Memory: {agent_metrics.get('memory_mb', 0):.1f} MB")
        print(f"      Threads: {agent_metrics.get('num_threads', 0)}")


def print_decisions_section(decisions):
    """Print recent decisions section"""
    print("\n🧠 RECENT DECISIONS | القرارات الأخيرة")
    print("-" * 80)
    
    print(f"   {decisions['arabic_summary']}")
    
    if decisions['decisions']:
        print("\n   Latest Decisions:")
        for i, decision in enumerate(decisions['decisions'][:5], 1):
            decision_emoji = "✅" if decision.get('action_executed') else "⏸️"
            print(f"      {decision_emoji} {i}. [{decision['cycle_id'][:8]}...] "
                  f"{decision['arabic_type']}")
            if decision.get('observations_collected'):
                print(f"         Observations: {decision['observations_collected']}")


async def monitor_loop(interval=5):
    """Main monitoring loop"""
    try:
        while True:
            clear_screen()
            print_header()
            
            try:
                # Fetch all data
                status = await get_agent_status()
                health = await get_agent_health()
                metrics = await get_agent_metrics()
                decisions = await get_recent_decisions(limit=10)
                
                # Display sections
                print_status_section(status)
                print_health_section(health)
                print_metrics_section(metrics)
                print_decisions_section(decisions)
                
                print("\n" + "=" * 80)
                print(f"🔄 Refreshing every {interval}s... Press Ctrl+C to exit")
                print("=" * 80)
                
            except Exception as e:
                print(f"\n❌ Error fetching data: {e}")
            
            await asyncio.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped. Goodbye!")
        sys.exit(0)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Noogh Agent Real-time Monitoring Dashboard"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Refresh interval in seconds (default: 5)"
    )
    
    args = parser.parse_args()
    
    print("🚀 Starting Noogh Agent Monitor...")
    print(f"   Refresh interval: {args.interval}s")
    print("   Press Ctrl+C to exit\n")
    
    asyncio.run(monitor_loop(interval=args.interval))


if __name__ == "__main__":
    main()
