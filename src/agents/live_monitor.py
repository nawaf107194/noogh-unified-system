#!/usr/bin/env python3
"""
Live System Monitor - مراقب النظام الحي
يراقب NOOGH بشكل مستمر ويعرض التحديثات الفورية
"""

import sys
import time
import sqlite3
from pathlib import Path
from datetime import datetime
from collections import deque

sys.path.insert(0, str(Path(__file__).parent.parent))

from unified_core.core.decision_persistence import get_decision_persistence

# Colors
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RESET = "\033[0m"
BOLD = "\033[1m"
CLEAR = "\033[2J\033[H"


class LiveMonitor:
    """مراقب حي للنظام"""

    def __init__(self):
        self.db_path = Path(__file__).parent.parent / 'data' / 'shared_memory.sqlite'
        self.persistence = get_decision_persistence()
        self.last_decision_count = 0
        self.last_trade_count = 0
        self.decision_history = deque(maxlen=10)
        self.trade_history = deque(maxlen=5)

    def get_system_status(self):
        """حالة النظام"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        status = {}

        # Beliefs
        cursor.execute("SELECT COUNT(*) as count FROM beliefs")
        status['beliefs'] = cursor.fetchone()['count']

        # Observations
        cursor.execute("SELECT COUNT(*) as count FROM observations")
        status['observations'] = cursor.fetchone()['count']

        # Decisions
        cursor.execute("SELECT COUNT(*) as count FROM decisions")
        status['decisions'] = cursor.fetchone()['count']

        # Goals
        try:
            cursor.execute("SELECT COUNT(*) as count FROM goals")
            status['goals'] = cursor.fetchone()['count']
        except:
            status['goals'] = 0

        conn.close()
        return status

    def get_recent_decisions(self, limit=5):
        """أحدث القرارات"""
        return self.persistence.get_recent_decisions(limit)

    def get_trading_status(self):
        """حالة التداول"""
        trade_file = Path(__file__).parent.parent / 'data' / 'trading' / 'trade_history.json'

        if not trade_file.exists():
            return None

        import json
        with open(trade_file, 'r') as f:
            data = json.load(f)

        stats = data.get('stats', {})
        total = stats.get('total', 0)
        wins = stats.get('wins', 0)

        # Calculate win_rate
        win_rate = (wins / total * 100) if total > 0 else 0

        return {
            'total_trades': total,
            'wins': wins,
            'losses': stats.get('losses', 0),
            'win_rate': win_rate,
            'total_pnl': stats.get('total_pnl', 0),
            'recent': data.get('history', [])[:5]
        }

    def get_neuron_stats(self):
        """إحصائيات العصبونات"""
        try:
            from unified_core.core.neuron_fabric import get_neuron_fabric
            fabric = get_neuron_fabric()

            if hasattr(fabric, '_neurons'):
                neurons = fabric._neurons
                total = len(neurons)
                active = sum(1 for n in neurons.values() if n.energy > 0.5)
                avg_energy = sum(n.energy for n in neurons.values()) / total if total > 0 else 0

                return {
                    'total': total,
                    'active': active,
                    'avg_energy': avg_energy
                }
        except:
            pass

        return {'total': 0, 'active': 0, 'avg_energy': 0}

    def detect_new_decisions(self, current_count):
        """كشف القرارات الجديدة"""
        if current_count > self.last_decision_count:
            new_count = current_count - self.last_decision_count
            self.last_decision_count = current_count
            return new_count
        self.last_decision_count = current_count
        return 0

    def detect_new_trades(self, current_count):
        """كشف الصفقات الجديدة"""
        if current_count > self.last_trade_count:
            new_count = current_count - self.last_trade_count
            self.last_trade_count = current_count
            return new_count
        self.last_trade_count = current_count
        return 0

    def print_header(self):
        """طباعة الرأسية"""
        print(f"{CLEAR}")
        print(f"{CYAN}{BOLD}╔═══════════════════════════════════════════════════════════════════╗{RESET}")
        print(f"{CYAN}{BOLD}║          🧠 NOOGH LIVE MONITOR - المراقب الحي 🧠                 ║{RESET}")
        print(f"{CYAN}{BOLD}║  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                                            ║{RESET}")
        print(f"{CYAN}{BOLD}╚═══════════════════════════════════════════════════════════════════╝{RESET}\n")

    def print_system_status(self, status):
        """طباعة حالة النظام"""
        print(f"{YELLOW}{BOLD}📊 SYSTEM STATUS{RESET}")
        print(f"  {GREEN}Beliefs:{RESET} {status['beliefs']:,}")
        print(f"  {GREEN}Observations:{RESET} {status['observations']:,}")
        print(f"  {GREEN}Decisions:{RESET} {status['decisions']:,}")
        print(f"  {GREEN}Goals:{RESET} {status['goals']:,}")

    def print_neuron_stats(self, stats):
        """طباعة إحصائيات العصبونات"""
        print(f"\n{YELLOW}{BOLD}🧬 NEURON FABRIC{RESET}")
        print(f"  {GREEN}Total Neurons:{RESET} {stats['total']:,}")
        print(f"  {GREEN}Active:{RESET} {stats['active']:,} ({stats['active']/stats['total']*100:.1f}%)" if stats['total'] > 0 else f"  {GREEN}Active:{RESET} 0")
        print(f"  {GREEN}Avg Energy:{RESET} {stats['avg_energy']:.3f}")

    def print_trading_status(self, trading):
        """طباعة حالة التداول"""
        print(f"\n{YELLOW}{BOLD}📈 TRADING STATUS{RESET}")
        if trading:
            win_rate_color = GREEN if trading['win_rate'] >= 60 else (YELLOW if trading['win_rate'] >= 50 else RED)
            pnl_color = GREEN if trading['total_pnl'] > 0 else RED

            print(f"  {GREEN}Total Trades:{RESET} {trading['total_trades']:,}")
            print(f"  {win_rate_color}Win Rate:{RESET} {trading['win_rate']:.1f}%")
            print(f"  {pnl_color}Total PnL:{RESET} ${trading['total_pnl']:,.2f}")
        else:
            print(f"  {YELLOW}No trading data{RESET}")

    def print_recent_decisions(self, decisions):
        """طباعة القرارات الأخيرة"""
        print(f"\n{YELLOW}{BOLD}🧠 RECENT DECISIONS (Last 5){RESET}")
        if decisions:
            for i, dec in enumerate(decisions, 1):
                query_short = dec['query'][:45] if dec['query'] else 'N/A'
                print(f"  {i}. {CYAN}{dec['decision_id'][:8]}...{RESET} | {query_short}")
                print(f"     Action: {dec['action_type']} | Cost: {dec['cost_paid']:.1f}")
        else:
            print(f"  {YELLOW}No decisions yet{RESET}")

    def print_recent_trades(self, trades):
        """طباعة الصفقات الأخيرة"""
        print(f"\n{YELLOW}{BOLD}💰 RECENT TRADES (Last 5){RESET}")
        if trades:
            for i, trade in enumerate(trades, 1):
                pnl = trade.get('pnl_percent', 0)
                pnl_color = GREEN if pnl > 0 else RED
                status = trade.get('status', 'UNKNOWN')

                print(f"  {i}. {trade['symbol']} {trade['direction']} | "
                      f"{pnl_color}{pnl:+.2f}%{RESET} | {status}")
        else:
            print(f"  {YELLOW}No trades yet{RESET}")

    def print_activity_log(self, new_decisions, new_trades):
        """طباعة سجل النشاط"""
        print(f"\n{YELLOW}{BOLD}📋 ACTIVITY LOG{RESET}")

        if new_decisions > 0:
            print(f"  {GREEN}🆕 {new_decisions} new decision(s) made!{RESET}")

        if new_trades > 0:
            print(f"  {GREEN}🆕 {new_trades} new trade(s) executed!{RESET}")

        if new_decisions == 0 and new_trades == 0:
            print(f"  {YELLOW}No new activity in the last cycle{RESET}")

    def run(self, interval=5):
        """تشغيل المراقب"""
        print(f"{GREEN}Starting Live Monitor... (Press Ctrl+C to stop){RESET}\n")
        time.sleep(2)

        try:
            while True:
                # Get data
                status = self.get_system_status()
                neuron_stats = self.get_neuron_stats()
                trading = self.get_trading_status()
                decisions = self.get_recent_decisions(5)

                # Detect new activity
                new_decisions = self.detect_new_decisions(status['decisions'])
                new_trades = 0
                if trading:
                    new_trades = self.detect_new_trades(trading['total_trades'])

                # Print dashboard
                self.print_header()
                self.print_system_status(status)
                self.print_neuron_stats(neuron_stats)
                self.print_trading_status(trading)
                self.print_recent_decisions(decisions)

                if trading and trading['recent']:
                    self.print_recent_trades(trading['recent'])

                self.print_activity_log(new_decisions, new_trades)

                # Footer
                print(f"\n{CYAN}Refreshing every {interval}s... (Ctrl+C to stop){RESET}")

                # Wait
                time.sleep(interval)

        except KeyboardInterrupt:
            print(f"\n\n{GREEN}Monitor stopped by user{RESET}")
            print(f"{CYAN}Final Stats:{RESET}")
            print(f"  Total Decisions: {status['decisions']:,}")
            print(f"  Total Trades: {trading['total_trades']:,}" if trading else "  No trades")
            print(f"\n{GREEN}Goodbye! 👋{RESET}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="NOOGH Live System Monitor")
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Refresh interval in seconds (default: 5)"
    )

    args = parser.parse_args()

    monitor = LiveMonitor()
    monitor.run(interval=args.interval)
