#!/usr/bin/env python3
"""
Decision Viewer - عارض القرارات
يعرض جميع القرارات المُتخذة من DecisionScorer
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from unified_core.core.decision_persistence import get_decision_persistence

# Colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_header(title: str):
    """طباعة رأسية"""
    print(f"\n{CYAN}{BOLD}{'='*70}{RESET}")
    print(f"{CYAN}{BOLD}{title:^70}{RESET}")
    print(f"{CYAN}{BOLD}{'='*70}{RESET}\n")


def main():
    """عرض القرارات"""

    print(f"\n{CYAN}{BOLD}╔═══════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{CYAN}{BOLD}║              🧠 DECISION VIEWER - عارض القرارات 🧠               ║{RESET}")
    print(f"{CYAN}{BOLD}╚═══════════════════════════════════════════════════════════════════╝{RESET}\n")

    # Initialize persistence
    persistence = get_decision_persistence()

    # Get stats
    print_header("📊 DECISION STATISTICS")
    stats = persistence.get_stats()

    print(f"{GREEN}Total Decisions: {stats.get('total_decisions', 0):,}{RESET}")
    print(f"{GREEN}Recent (24h): {stats.get('recent_24h', 0):,}{RESET}")
    print(f"{GREEN}Average Cost: {stats.get('avg_cost', 0):.2f}{RESET}")

    print(f"\n{YELLOW}By Type:{RESET}")
    for dtype, count in stats.get('by_type', {}).items():
        print(f"  • {dtype}: {count:,}")

    # Get recent decisions
    print_header("🔍 RECENT DECISIONS (Last 20)")

    recent = persistence.get_recent_decisions(20)

    if not recent:
        print(f"{YELLOW}No decisions found{RESET}")
        return

    for i, decision in enumerate(recent, 1):
        # Color by type
        dtype = decision['decision_type']
        color = GREEN if dtype == 'action' else (YELLOW if dtype == 'abstain' else CYAN)

        print(f"\n{color}{BOLD}{i}. Decision {decision['decision_id'][:12]}...{RESET}")
        print(f"   Type: {dtype}")
        print(f"   Query: {decision['query'][:70]}")
        print(f"   Action: {decision['action_type']}")
        print(f"   Cost: {decision['cost_paid']:.2f}")
        print(f"   Beliefs: {len(decision['based_on_beliefs'])} used")
        print(f"   Constraints: {len(decision['constrained_by'])} applied")

        # Show content if interesting
        content = decision.get('content', {})
        params = content.get('params', {})
        if params and isinstance(params, dict):
            print(f"   Params: {list(params.keys())[:3]}")

    # Footer
    print(f"\n{CYAN}{BOLD}╔═══════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{CYAN}{BOLD}║         🧠 Decision History Complete - {len(recent)} shown 🧠         ║{RESET}")
    print(f"{CYAN}{BOLD}╚═══════════════════════════════════════════════════════════════════╝{RESET}\n")


if __name__ == "__main__":
    main()
