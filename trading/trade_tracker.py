"""
Daily Trade Tracker & Risk Management
Implements 30-day compounding strategy with strict capital rules
"""

import json
import logging
from datetime import datetime, date
from typing import Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class TradeStatus(Enum):
    """Trade status enum."""
    WIN = "WIN"
    LOSS = "LOSS"
    BREAKEVEN = "BREAKEVEN"
    OPEN = "OPEN"


@dataclass
class Trade:
    """Trade record."""
    trade_id: str
    symbol: str
    side: str  # 'LONG' or 'SHORT'
    entry_price: float
    quantity: float
    stop_loss: float
    take_profit: Dict[str, float]
    entry_time: str
    exit_price: Optional[float] = None
    exit_time: Optional[str] = None
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    status: str = TradeStatus.OPEN.value
    reasons: List[str] = None
    liquidity_score: float = 0
    indicator_strength: float = 0

    def __post_init__(self):
        if self.reasons is None:
            self.reasons = []


class DailyTracker:
    """Track daily trades and manage 30-day strategy."""

    def __init__(self, data_dir: str = "/home/noogh/projects/noogh_unified_system/data/trades"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.trades_file = self.data_dir / "trades.json"
        self.daily_file = self.data_dir / "daily_stats.json"
        self.capital_file = self.data_dir / "capital.json"

        self.trades: List[Trade] = []
        self.load_trades()

        # Capital Management
        self.total_capital = 20.0
        self.active_balance = 10.0
        self.reserve_balance = 10.0
        self.load_capital()

    def load_trades(self):
        """Load trades from file."""
        if self.trades_file.exists():
            try:
                with open(self.trades_file, 'r') as f:
                    data = json.load(f)
                    self.trades = [Trade(**t) for t in data]
            except Exception as e:
                logger.error(f"Error loading trades: {e}")
                self.trades = []

    def save_trades(self):
        """Save trades to file."""
        try:
            with open(self.trades_file, 'w') as f:
                json.dump([asdict(t) for t in self.trades], f, indent=2)
        except Exception as e:
            logger.error(f"Error saving trades: {e}")

    def load_capital(self):
        """Load capital info."""
        if self.capital_file.exists():
            try:
                with open(self.capital_file, 'r') as f:
                    data = json.load(f)
                    self.active_balance = data.get('active_balance', 10.0)
                    self.reserve_balance = data.get('reserve_balance', 10.0)
                    self.total_capital = self.active_balance + self.reserve_balance
            except Exception as e:
                logger.error(f"Error loading capital: {e}")

    def save_capital(self):
        """Save capital info."""
        try:
            data = {
                'total_capital': self.total_capital,
                'active_balance': self.active_balance,
                'reserve_balance': self.reserve_balance,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.capital_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving capital: {e}")

    def get_today_trades(self) -> List[Trade]:
        """Get today's trades."""
        today = date.today().isoformat()
        return [t for t in self.trades if t.entry_time.startswith(today)]

    def get_today_stats(self) -> Dict:
        """
        Get today's trading statistics.

        Returns:
            Dict with wins, losses, profit, etc.
        """
        today_trades = self.get_today_trades()

        wins = [t for t in today_trades if t.status == TradeStatus.WIN.value]
        losses = [t for t in today_trades if t.status == TradeStatus.LOSS.value]
        open_trades = [t for t in today_trades if t.status == TradeStatus.OPEN.value]

        total_pnl = sum(t.pnl for t in today_trades if t.pnl)

        return {
            'date': date.today().isoformat(),
            'total_trades': len(today_trades),
            'wins': len(wins),
            'losses': len(losses),
            'open_trades': len(open_trades),
            'win_rate': (len(wins) / len(today_trades) * 100) if today_trades else 0,
            'total_pnl': total_pnl,
            'active_balance': self.active_balance,
            'reserve_balance': self.reserve_balance
        }

    def can_trade_today(self) -> Dict:
        """
        Check if trading is allowed today based on rules.

        Rules:
        - Maximum 3 trades per day
        - Stop if 1 Win + 2 Losses (Scenario B)
        - Reserve balance cannot be touched

        Returns:
            Dict with 'allowed' (bool) and 'reason' (str)
        """
        stats = self.get_today_stats()

        # Rule 1: Max 3 trades per day
        if stats['total_trades'] >= 3:
            return {
                'allowed': False,
                'reason': 'Daily trade limit reached (3/3)'
            }

        # Rule 2: Scenario B - 1 Win + 2 Losses = HALT
        if stats['wins'] >= 1 and stats['losses'] >= 2:
            return {
                'allowed': False,
                'reason': '🛑 SCENARIO B: 1 Win + 2 Losses - Trading halted for today'
            }

        # Rule 3: Check active balance
        if self.active_balance < 1.0:  # Minimum $1 to trade
            return {
                'allowed': False,
                'reason': '⚠️ Active balance too low (< $1)'
            }

        # Rule 4: Reserve balance protection
        if self.reserve_balance < 10.0:
            return {
                'allowed': False,
                'reason': '🚨 CRITICAL: Reserve balance below $10 - System locked!'
            }

        return {
            'allowed': True,
            'reason': f'Trading allowed ({stats["total_trades"]}/3 trades today)'
        }

    def should_use_trailing_stop(self) -> bool:
        """
        Check if Trailing Stop should be activated (Scenario A).

        Scenario A: 2 Wins + 1 Loss = Use trailing stop on next TP
        """
        stats = self.get_today_stats()
        return stats['wins'] >= 2 and stats['losses'] >= 1

    def add_trade(self, trade: Trade):
        """Add a new trade."""
        self.trades.append(trade)
        self.save_trades()
        logger.info(f"✅ Trade added: {trade.trade_id}")

    def close_trade(self, trade_id: str, exit_price: float, pnl: float):
        """
        Close a trade and update balance.

        Args:
            trade_id: Trade ID
            exit_price: Exit price
            pnl: Profit/Loss amount
        """
        trade = next((t for t in self.trades if t.trade_id == trade_id), None)

        if not trade:
            logger.error(f"Trade {trade_id} not found")
            return

        trade.exit_price = exit_price
        trade.exit_time = datetime.now().isoformat()
        trade.pnl = pnl
        trade.pnl_pct = (pnl / (trade.entry_price * trade.quantity)) * 100

        # Determine status
        if pnl > 0:
            trade.status = TradeStatus.WIN.value
        elif pnl < 0:
            trade.status = TradeStatus.LOSS.value
        else:
            trade.status = TradeStatus.BREAKEVEN.value

        # Update active balance (compounding!)
        self.active_balance += pnl

        # Save
        self.save_trades()
        self.save_capital()

        logger.info(f"✅ Trade closed: {trade_id} | PnL: ${pnl:+.2f} | New balance: ${self.active_balance:.2f}")

    def calculate_position_size(self, risk_pct: float = 1.0) -> float:
        """
        Calculate position size based on risk percentage.

        Args:
            risk_pct: Percentage of active balance to risk (default 1%)

        Returns:
            Position size in USDT
        """
        return (self.active_balance * risk_pct) / 100

    def get_30day_performance(self) -> Dict:
        """
        Get 30-day performance summary.

        Returns:
            Dict with stats
        """
        from datetime import timedelta

        thirty_days_ago = (datetime.now() - timedelta(days=30)).date().isoformat()
        recent_trades = [t for t in self.trades if t.entry_time >= thirty_days_ago]

        wins = [t for t in recent_trades if t.status == TradeStatus.WIN.value]
        losses = [t for t in recent_trades if t.status == TradeStatus.LOSS.value]

        total_pnl = sum(t.pnl for t in recent_trades if t.pnl)

        # Calculate daily avg
        days_trading = min(30, len(set(t.entry_time[:10] for t in recent_trades)))
        daily_avg = total_pnl / days_trading if days_trading > 0 else 0

        # ROI
        initial_balance = 10.0  # Starting active balance
        roi = ((self.active_balance - initial_balance) / initial_balance) * 100

        return {
            'period': '30 days',
            'total_trades': len(recent_trades),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': (len(wins) / len(recent_trades) * 100) if recent_trades else 0,
            'total_pnl': total_pnl,
            'daily_avg_pnl': daily_avg,
            'roi': roi,
            'starting_balance': initial_balance,
            'current_balance': self.active_balance,
            'days_trading': days_trading
        }

    def get_dashboard_summary(self) -> Dict:
        """Get comprehensive dashboard summary."""
        today_stats = self.get_today_stats()
        thirty_day = self.get_30day_performance()
        can_trade = self.can_trade_today()
        use_trailing = self.should_use_trailing_stop()

        return {
            'capital': {
                'total': self.total_capital,
                'active': self.active_balance,
                'reserve': self.reserve_balance,
                'reserve_protected': self.reserve_balance >= 10.0
            },
            'today': today_stats,
            'thirty_day': thirty_day,
            'trading_status': can_trade,
            'trailing_stop_mode': use_trailing,
            'timestamp': datetime.now().isoformat()
        }


# Singleton instance
_tracker = None

def get_trade_tracker() -> DailyTracker:
    """Get or create tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = DailyTracker()
    return _tracker
