#!/usr/bin/env python3
"""
Quick System Health Check
Run: python scripts/health_check.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unified_core.health.system_health_monitor import get_system_health_monitor, HealthStatus

def main():
    print("=" * 70)
    print("🏥 NOOGH System Health Check")
    print("=" * 70)
    print()

    monitor = get_system_health_monitor()
    result = monitor.run_all_checks()

    # Status emoji
    status_emoji = {
        "healthy": "✅",
        "warning": "⚠️",
        "critical": "🚨",
        "unknown": "❓"
    }

    print(f"Overall Status: {status_emoji.get(result['status'], '❓')} {result['status'].upper()}")
    print()

    if not result['issues']:
        print("✨ All systems nominal!")
        print()
        return 0

    # Group by severity
    critical = [i for i in result['issues'] if i['severity'] == 'critical']
    warnings = [i for i in result['issues'] if i['severity'] == 'warning']

    if critical:
        print(f"🚨 CRITICAL ISSUES ({len(critical)}):")
        print("-" * 70)
        for issue in critical:
            print(f"\n❌ {issue['message']}")
            if issue.get('fix_suggestion'):
                print(f"   💡 Fix: {issue['fix_suggestion']}")
        print()

    if warnings:
        print(f"⚠️  WARNINGS ({len(warnings)}):")
        print("-" * 70)
        for issue in warnings:
            print(f"\n⚠️  {issue['message']}")
            if issue.get('fix_suggestion'):
                print(f"   💡 Fix: {issue['fix_suggestion']}")
            if issue.get('auto_fixable'):
                print(f"   🔧 Auto-fixable: Yes")
        print()

    print("=" * 70)
    print(f"Total Issues: {len(result['issues'])} ({len(critical)} critical, {len(warnings)} warnings)")
    print("=" * 70)

    return 1 if critical else 0


if __name__ == "__main__":
    sys.exit(main())
