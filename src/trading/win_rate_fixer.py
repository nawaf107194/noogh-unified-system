#!/usr/bin/env python3
"""
Win Rate Fixer - مصلح Win Rate
يصلح حساب Win Rate الخاطئ ويحدث الإحصائيات

المشكلة: Win Rate = 0% بينما PnL إيجابي
الحل: إعادة حساب Win Rate من سجل الصفقات
"""

import sys
import sqlite3
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)


class WinRateFixer:
    """مصلح Win Rate"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = str(Path(__file__).parent.parent / 'data' / 'shared_memory.sqlite')
        
        self.db_path = db_path
        logger.info(f"💾 Database: {db_path}")
    
    def analyze_trades(self) -> dict:
        """تحليل الصفقات وحساب الإحصائيات الصحيحة"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if trades table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='trades'
            """)
            
            if not cursor.fetchone():
                logger.warning("⚠️  No 'trades' table found")
                return None
            
            # Get all trades
            cursor.execute("""
                SELECT 
                    symbol,
                    side,
                    pnl_pct,
                    pnl_usd,
                    exit_reason,
                    entry_time,
                    exit_time
                FROM trades
                WHERE exit_time IS NOT NULL
                ORDER BY exit_time DESC
            """)
            
            trades = cursor.fetchall()
            
            if not trades:
                logger.warning("⚠️  No closed trades found")
                return None
            
            # Calculate statistics
            total_trades = len(trades)
            winning_trades = [t for t in trades if t[2] > 0]  # pnl_pct > 0
            losing_trades = [t for t in trades if t[2] < 0]
            breakeven_trades = [t for t in trades if t[2] == 0]
            
            total_wins = len(winning_trades)
            total_losses = len(losing_trades)
            total_breakeven = len(breakeven_trades)
            
            win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
            
            total_pnl_usd = sum(t[3] for t in trades if t[3] is not None)
            avg_win = sum(t[3] for t in winning_trades if t[3]) / total_wins if total_wins > 0 else 0
            avg_loss = sum(t[3] for t in losing_trades if t[3]) / total_losses if total_losses > 0 else 0
            
            # Profit factor
            total_win_usd = sum(t[3] for t in winning_trades if t[3])
            total_loss_usd = abs(sum(t[3] for t in losing_trades if t[3]))
            profit_factor = total_win_usd / total_loss_usd if total_loss_usd > 0 else 0
            
            stats = {
                'total_trades': total_trades,
                'winning_trades': total_wins,
                'losing_trades': total_losses,
                'breakeven_trades': total_breakeven,
                'win_rate': win_rate,
                'total_pnl_usd': total_pnl_usd,
                'avg_win_usd': avg_win,
                'avg_loss_usd': avg_loss,
                'profit_factor': profit_factor,
                'recent_5': trades[:5]
            }
            
            return stats
            
        finally:
            conn.close()
    
    def fix_win_rate_in_beliefs(self, stats: dict):
        """تحديث Win Rate في beliefs"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Update or insert trading stats belief
            trading_stats_key = 'system:trading_stats'
            
            cursor.execute("""
                INSERT OR REPLACE INTO beliefs (key, value, utility_score, updated_at)
                VALUES (?, ?, ?, ?)
            """, (
                trading_stats_key,
                str({
                    'total_trades': stats['total_trades'],
                    'win_rate': stats['win_rate'],
                    'total_pnl_usd': stats['total_pnl_usd'],
                    'profit_factor': stats['profit_factor'],
                    'updated_at': datetime.now().isoformat()
                }),
                0.99,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            logger.info(f"✅ Updated trading stats in beliefs: win_rate={stats['win_rate']:.2f}%")
            
        finally:
            conn.close()
    
    def print_report(self, stats: dict):
        """طباعة التقرير"""
        print(f"\n{'='*80}")
        print("📊 TRADING STATISTICS REPORT")
        print(f"{'='*80}\n")
        
        print(f"Total Trades       : {stats['total_trades']:,}")
        print(f"Winning Trades     : {stats['winning_trades']:,}")
        print(f"Losing Trades      : {stats['losing_trades']:,}")
        print(f"Breakeven Trades   : {stats['breakeven_trades']:,}")
        print()
        print(f"Win Rate           : {stats['win_rate']:.2f}%")
        print(f"Total PnL          : ${stats['total_pnl_usd']:,.2f}")
        print(f"Average Win        : ${stats['avg_win_usd']:,.2f}")
        print(f"Average Loss       : ${stats['avg_loss_usd']:,.2f}")
        print(f"Profit Factor      : {stats['profit_factor']:.2f}")
        
        print(f"\n{'='*80}")
        print("📊 RECENT 5 TRADES")
        print(f"{'='*80}\n")
        
        for i, trade in enumerate(stats['recent_5'], 1):
            symbol, side, pnl_pct, pnl_usd, reason, entry, exit = trade
            status = '🟢' if pnl_pct > 0 else '🔴' if pnl_pct < 0 else '⚪'
            print(f"{i}. {status} {symbol} {side} | {pnl_pct:+.2f}% (${pnl_usd:+.2f}) | {reason}")
        
        print(f"\n{'='*80}\n")
    
    def run(self):
        """تشغيل المصلح"""
        logger.info("\n🔧 Starting Win Rate Fixer...\n")
        
        # 1. Analyze trades
        stats = self.analyze_trades()
        
        if not stats:
            logger.error("❌ Cannot analyze trades - no data found")
            return
        
        # 2. Print report
        self.print_report(stats)
        
        # 3. Fix beliefs
        self.fix_win_rate_in_beliefs(stats)
        
        logger.info("✅ Win Rate fixed successfully!\n")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix Win Rate calculation')
    parser.add_argument('--db', type=str, help='Database path')
    
    args = parser.parse_args()
    
    fixer = WinRateFixer(db_path=args.db)
    fixer.run()


if __name__ == '__main__':
    main()
