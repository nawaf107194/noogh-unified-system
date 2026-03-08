#!/usr/bin/env python3
"""
Paper Trades Analyzer - محلل الصفقات الورقية
يحلل paper_trades ويحسب Win Rate بشكل صحيح

ملاحظة:
- exit_price و pnl دائماً NULL
- نستخدم pnl_pct فقط
"""

import sys
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
import json
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)


class PaperTradesAnalyzer:
    """محلل الصفقات الورقية"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = str(Path(__file__).parent.parent / 'data' / 'shared_memory.sqlite')
        
        self.db_path = db_path
    
    def analyze_all(self) -> dict:
        """تحليل شامل"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get ALL paper trades
            cursor.execute("""
                SELECT 
                    id, symbol, side, entry_price, exit_price, quantity,
                    pnl, pnl_pct, brain_confidence, entry_time, exit_time, exit_reason
                FROM paper_trades
                ORDER BY created_at DESC
            """)
            
            all_trades = cursor.fetchall()
            
            # Separate by pnl_pct (not exit_time - it's always NULL!)
            closed_trades = [t for t in all_trades if t[7] is not None]  # pnl_pct exists
            
            logger.info(f"📊 Total: {len(all_trades)} | With pnl_pct: {len(closed_trades)}")
            
            if not closed_trades:
                logger.warning("⚠️  No trades with pnl_pct")
                return None
            
            # Analyze
            winning = [t for t in closed_trades if float(t[7]) > 0]
            losing = [t for t in closed_trades if float(t[7]) < 0]
            breakeven = [t for t in closed_trades if float(t[7]) == 0]
            
            total = len(closed_trades)
            wins = len(winning)
            losses = len(losing)
            
            win_rate = (wins / total * 100) if total > 0 else 0
            
            # PnL estimation
            avg_capital = 1000
            total_pnl = sum(float(t[7]) * avg_capital / 100 for t in closed_trades)
            avg_win_pct = sum(float(t[7]) for t in winning) / wins if wins > 0 else 0
            avg_loss_pct = sum(float(t[7]) for t in losing) / losses if losses > 0 else 0
            
            # Profit factor
            total_win_pct = sum(float(t[7]) for t in winning)
            total_loss_pct = abs(sum(float(t[7]) for t in losing))
            profit_factor = total_win_pct / total_loss_pct if total_loss_pct > 0 else 0
            
            # Breakdowns
            exit_reasons = Counter(t[11] for t in closed_trades if t[11])
            symbols = Counter(t[1] for t in closed_trades)
            sides = Counter(t[2] for t in closed_trades)
            
            return {
                'total_trades': total,
                'winning_trades': wins,
                'losing_trades': losses,
                'breakeven_trades': len(breakeven),
                'win_rate': win_rate,
                'total_pnl_estimate': total_pnl,
                'avg_win_pct': avg_win_pct,
                'avg_loss_pct': avg_loss_pct,
                'profit_factor': profit_factor,
                'exit_reasons': dict(exit_reasons.most_common(10)),
                'top_symbols': dict(symbols.most_common(10)),
                'sides': dict(sides),
                'recent_5': closed_trades[:5]
            }
            
        finally:
            conn.close()
    
    def print_report(self, stats: dict):
        """طباعة تقرير"""
        print(f"\n{'='*90}")
        print("📊 PAPER TRADING ANALYSIS")
        print(f"{'='*90}\n")
        
        print(f"Total Trades       : {stats['total_trades']:,}")
        print(f"Winning Trades     : {stats['winning_trades']:,}")
        print(f"Losing Trades      : {stats['losing_trades']:,}")
        print()
        print(f"Win Rate           : {stats['win_rate']:.2f}%")
        print(f"Profit Factor      : {stats['profit_factor']:.2f}")
        print(f"Avg Win            : +{stats['avg_win_pct']:.2f}%")
        print(f"Avg Loss           : {stats['avg_loss_pct']:.2f}%")
        print(f"Est. Total PnL     : ${stats['total_pnl_estimate']:,.2f}")
        
        print(f"\n{'='*90}")
        print("🔍 EXIT REASONS")
        print(f"{'='*90}\n")
        for reason, count in stats['exit_reasons'].items():
            pct = count / stats['total_trades'] * 100
            print(f"  {reason or 'UNKNOWN':<20} : {count:>4} ({pct:>5.1f}%)")
        
        print(f"\n{'='*90}")
        print("📊 TOP SYMBOLS")
        print(f"{'='*90}\n")
        for symbol, count in stats['top_symbols'].items():
            pct = count / stats['total_trades'] * 100
            print(f"  {symbol:<15} : {count:>4} ({pct:>5.1f}%)")
        
        print(f"\n{'='*90}\n")
    
    def run(self):
        logger.info("🔧 Starting Analysis...\n")
        
        stats = self.analyze_all()
        
        if not stats:
            logger.error("❌ No data")
            return
        
        self.print_report(stats)
        logger.info("✅ Done!\n")


if __name__ == '__main__':
    analyzer = PaperTradesAnalyzer()
    analyzer.run()
