#!/usr/bin/env python3
"""
Win Rate Fixer - مصلح Win Rate
يصلح حساب Win Rate الخاطئ ويحدث الإحصائيات

يدعم:
- جدول trades (للتداول الحقيقي)
- جدول paper_trades (للتداول الورقي)

الاستخدام:
  python3 trading/win_rate_fixer.py                    # Auto-detect
  python3 trading/win_rate_fixer.py --table trades     # Live trades
  python3 trading/win_rate_fixer.py --table paper_trades  # Paper trades
"""

import sys
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)


class WinRateFixer:
    """مصلح Win Rate"""
    
    def __init__(self, db_path: str = None, table_name: str = None):
        if db_path is None:
            db_path = str(Path(__file__).parent.parent / 'data' / 'shared_memory.sqlite')
        
        self.db_path = db_path
        self.table_name = table_name
        logger.info(f"💾 Database: {db_path}")
    
    def detect_trades_table(self) -> str:
        """كشف جدول الصفقات تلقائياً"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND (name='trades' OR name='paper_trades')
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            
            if 'paper_trades' in tables:
                logger.info("✅ Found 'paper_trades' table")
                return 'paper_trades'
            elif 'trades' in tables:
                logger.info("✅ Found 'trades' table")
                return 'trades'
            else:
                logger.warning("⚠️  No trades or paper_trades table found")
                return None
        finally:
            conn.close()
    
    def get_table_columns(self, table_name: str) -> list:
        """جلب أعمدة الجدول"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            return columns
        finally:
            conn.close()
    
    def analyze_trades(self, table_name: str = None) -> dict:
        """تحليل الصفقات وحساب الإحصائيات الصحيحة"""
        if table_name is None:
            table_name = self.table_name or self.detect_trades_table()
        
        if not table_name:
            return None
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get columns
            columns = self.get_table_columns(table_name)
            logger.info(f"📋 Columns in {table_name}: {', '.join(columns)}")
            
            # Build flexible query based on available columns
            # Common mappings
            symbol_col = 'symbol' if 'symbol' in columns else 'pair'
            side_col = 'side' if 'side' in columns else 'direction'
            
            # PnL columns (try multiple variations)
            pnl_pct_col = None
            for col in ['pnl_pct', 'pnl_percent', 'profit_pct', 'return_pct']:
                if col in columns:
                    pnl_pct_col = col
                    break
            
            pnl_usd_col = None
            for col in ['pnl_usd', 'pnl', 'profit', 'profit_usd']:
                if col in columns:
                    pnl_usd_col = col
                    break
            
            # Exit columns
            exit_reason_col = 'exit_reason' if 'exit_reason' in columns else 'status'
            exit_time_col = None
            for col in ['exit_time', 'closed_at', 'end_time']:
                if col in columns:
                    exit_time_col = col
                    break
            
            entry_time_col = None
            for col in ['entry_time', 'opened_at', 'start_time', 'timestamp']:
                if col in columns:
                    entry_time_col = col
                    break
            
            if not pnl_pct_col and not pnl_usd_col:
                logger.error("❌ No PnL column found")
                return None
            
            # Build query
            select_cols = [
                symbol_col,
                side_col,
                pnl_pct_col or "0",
                pnl_usd_col or "0",
                exit_reason_col if exit_reason_col in columns else "'UNKNOWN'",
                entry_time_col or "''",
                exit_time_col or "''"
            ]
            
            query = f"""
                SELECT {', '.join(select_cols)}
                FROM {table_name}
            """
            
            # Add WHERE clause if exit_time exists
            if exit_time_col:
                query += f" WHERE {exit_time_col} IS NOT NULL"
            
            query += f" ORDER BY {entry_time_col or 'rowid'} DESC"
            
            logger.info(f"🔍 Query: {query}")
            cursor.execute(query)
            trades = cursor.fetchall()
            
            if not trades:
                logger.warning(f"⚠️  No closed trades found in {table_name}")
                return None
            
            logger.info(f"📊 Found {len(trades)} trades")
            
            # Calculate statistics
            total_trades = len(trades)
            winning_trades = [t for t in trades if float(t[2] or 0) > 0]
            losing_trades = [t for t in trades if float(t[2] or 0) < 0]
            breakeven_trades = [t for t in trades if float(t[2] or 0) == 0]
            
            total_wins = len(winning_trades)
            total_losses = len(losing_trades)
            total_breakeven = len(breakeven_trades)
            
            win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
            
            total_pnl_usd = sum(float(t[3] or 0) for t in trades)
            avg_win = sum(float(t[3] or 0) for t in winning_trades) / total_wins if total_wins > 0 else 0
            avg_loss = sum(float(t[3] or 0) for t in losing_trades) / total_losses if total_losses > 0 else 0
            
            # Profit factor
            total_win_usd = sum(float(t[3] or 0) for t in winning_trades)
            total_loss_usd = abs(sum(float(t[3] or 0) for t in losing_trades))
            profit_factor = total_win_usd / total_loss_usd if total_loss_usd > 0 else 0
            
            stats = {
                'table_name': table_name,
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
            
        except Exception as e:
            logger.error(f"❌ Error analyzing trades: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            conn.close()
    
    def fix_win_rate_in_beliefs(self, stats: dict):
        """تحديث Win Rate في beliefs"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Update or insert trading stats belief
            trading_stats_key = f"system:trading_stats_{stats['table_name']}"
            
            value_dict = {
                'table': stats['table_name'],
                'total_trades': stats['total_trades'],
                'win_rate': stats['win_rate'],
                'total_pnl_usd': stats['total_pnl_usd'],
                'profit_factor': stats['profit_factor'],
                'updated_at': datetime.now().isoformat()
            }
            
            cursor.execute("""
                INSERT OR REPLACE INTO beliefs (key, value, utility_score, updated_at)
                VALUES (?, ?, ?, ?)
            """, (
                trading_stats_key,
                json.dumps(value_dict),
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
        print(f"📊 TRADING STATISTICS REPORT - {stats['table_name'].upper()}")
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
            pnl_pct = float(pnl_pct or 0)
            pnl_usd = float(pnl_usd or 0)
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
    parser.add_argument('--table', type=str, choices=['trades', 'paper_trades'], 
                        help='Trades table name (auto-detect if not specified)')
    
    args = parser.parse_args()
    
    fixer = WinRateFixer(db_path=args.db, table_name=args.table)
    fixer.run()


if __name__ == '__main__':
    main()
