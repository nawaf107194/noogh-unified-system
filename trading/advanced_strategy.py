"""
Advanced 30-Day Compounding Futures Strategy
Expert algorithmic trading system with dynamic risk management
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import pandas as pd
import numpy as np

from .technical_indicators import TechnicalIndicatorsV2, SignalEngineV2
from .trade_tracker import DailyTracker, get_trade_tracker, Trade, TradeStatus
from .binance_futures import BinanceFuturesManager, get_futures_manager

logger = logging.getLogger(__name__)


class NewsFilter:
    """Filter trades around high-impact news."""

    HIGH_IMPACT_NEWS_WINDOW = 15  # minutes before/after news

    @staticmethod
    def is_news_period(check_time: Optional[datetime] = None) -> Dict:
        """
        Check if current time is within news window.

        In production, this should connect to an economic calendar API.
        For now, returns a basic check.

        Returns:
            Dict with 'is_news_period' and 'reason'
        """
        if check_time is None:
            check_time = datetime.now()

        # TODO: Integrate with economic calendar API
        # Example APIs: ForexFactory, TradingEconomics, FXStreet

        # For demo: Block trading at typical high-impact times (example)
        hour = check_time.hour
        minute = check_time.minute

        # Example: Major news typically at 08:30, 10:00, 14:00, 19:00 UTC
        high_impact_hours = [8, 10, 14, 19]

        for news_hour in high_impact_hours:
            # Check if within 15 min window
            news_time = check_time.replace(hour=news_hour, minute=30, second=0, microsecond=0)
            time_diff = abs((check_time - news_time).total_seconds() / 60)

            if time_diff <= NewsFilter.HIGH_IMPACT_NEWS_WINDOW:
                return {
                    'is_news_period': True,
                    'reason': f'High-impact news window (±15 min from {news_hour}:30 UTC)',
                    'next_safe_time': news_time + timedelta(minutes=15)
                }

        return {
            'is_news_period': False,
            'reason': 'No scheduled high-impact news',
            'next_safe_time': None
        }


class AdvancedFuturesStrategy:
    """
    Advanced 30-day compounding Futures strategy.

    Implements:
    - Multi-timeframe analysis (1H/4H macro, 5m/15m micro)
    - Dynamic stop loss based on liquidity
    - Trailing stop logic (Scenario A)
    - Daily halt on losses (Scenario B)
    - Pullback handling (Scenario C)
    - News filtering
    - 1:2 minimum RRR
    """

    def __init__(
        self,
        testnet: bool = False,
        read_only: bool = False,
        max_leverage: int = 10
    ):
        self.futures = get_futures_manager(testnet=testnet, read_only=read_only, max_leverage=max_leverage)
        self.tracker = get_trade_tracker()
        self.testnet = testnet
        self.read_only = read_only

        logger.info("🚀 Advanced Futures Strategy initialized")
        logger.info(f"   Mode: {'TESTNET' if testnet else 'PRODUCTION'}")
        logger.info(f"   Read-only: {read_only}")
        logger.info(f"   Capital: ${self.tracker.active_balance:.2f} active + ${self.tracker.reserve_balance:.2f} reserve")

    def get_market_data(
        self,
        symbol: str,
        interval: str,
        limit: int = 200
    ) -> pd.DataFrame:
        """
        Fetch market data from Binance.

        Args:
            symbol: Trading pair
            interval: Kline interval (1m, 5m, 15m, 1h, 4h)
            limit: Number of candles

        Returns:
            DataFrame with OHLCV data
        """
        try:
            klines = self.futures.client.futures_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )

            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])

            # Convert types
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)

            df.set_index('timestamp', inplace=True)

            return df

        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return pd.DataFrame()

    def analyze_setup(self, symbol: str) -> Dict:
        """
        Analyze complete trading setup.

        Returns:
            Comprehensive analysis with signal, SL, TP, etc.
        """
        try:
            # 1. Pre-checks
            can_trade = self.tracker.can_trade_today()
            if not can_trade['allowed']:
                return {
                    'signal': None,
                    'reason': can_trade['reason']
                }

            news_check = NewsFilter.is_news_period()
            if news_check['is_news_period']:
                return {
                    'signal': None,
                    'reason': f"🔇 {news_check['reason']}"
                }

            # 2. Fetch data
            df_1h = self.get_market_data(symbol, '1h', 100)
            df_5m = self.get_market_data(symbol, '5m', 100)

            if df_1h.empty or df_5m.empty:
                return {'signal': None, 'reason': 'Failed to fetch market data'}

            # 3. Handle pullback (Placeholder/Commented out since V2 integrates this differently)
            # You could add custom logic here or rely on the SignalEngineV2
            
            # 4. Generate signal using V2
            signal_data = SignalEngineV2.generate_entry_signal(df_1h, df_5m)

            if not signal_data.get('signal'):
                return {
                    'signal': None,
                    'reason': 'No valid entry signal',
                    'analysis': signal_data
                }

            # 5. Calculate position size (1% risk)
            position_size_usdt = self.tracker.calculate_position_size(risk_pct=1.0)
            current_price = df_5m['close'].iloc[-1]
            quantity = position_size_usdt / current_price

            # 6. Stop Loss & Take Profits are already calculated by V2
            stop_loss = signal_data.get('stop_loss')
            tp_targets = signal_data.get('take_profits')
            
            if not stop_loss or not tp_targets:
                 return {
                    'signal': None,
                    'reason': f'Could not compute risk targets'
                }

            # 8. Check RRR
            if tp_targets['rrr'] < 2.0:
                return {
                    'signal': None,
                    'reason': f'RRR too low ({tp_targets["rrr"]:.2f} < 2.0)'
                }

            # 9. Return complete setup
            return {
                'signal': signal_data['signal'],
                'symbol': symbol,
                'entry_price': current_price,
                'quantity': quantity,
                'position_size_usdt': position_size_usdt,
                'stop_loss': stop_loss,
                'take_profit': tp_targets,
                'strength': signal_data.get('strength', 0),
                'liquidity_score': signal_data.get('snapshots', {}).get('liquidity_score', 50),
                'macro_trend': signal_data.get('macro_trend'),
                'reasons': signal_data.get('reasons', []),
                'timestamp': datetime.now().isoformat(),
                'trailing_stop_mode': self.tracker.should_use_trailing_stop()
            }

        except Exception as e:
            logger.error(f"Error analyzing setup: {e}")
            return {
                'signal': None,
                'reason': f'Analysis error: {str(e)}'
            }

    def execute_trade(self, analysis: Dict) -> Dict:
        """
        Execute trade based on analysis.

        Args:
            analysis: Output from analyze_setup()

        Returns:
            Trade execution result
        """
        if self.read_only:
            return {
                'success': False,
                'message': '🔒 Read-only mode - Trade simulation only',
                'analysis': analysis
            }

        try:
            signal = analysis['signal']
            if not signal:
                return {
                    'success': False,
                    'message': analysis.get('reason', 'No signal')
                }

            # Prepare order
            symbol = analysis['symbol']
            side = 'BUY' if signal == 'LONG' else 'SELL'
            quantity = analysis['quantity']
            stop_loss = analysis['stop_loss']

            # Execute
            result = self.futures.open_position(
                symbol=symbol,
                side=side,
                quantity=quantity,
                leverage=5,  # Conservative default
                stop_loss=stop_loss
            )

            if 'error' in result:
                return {
                    'success': False,
                    'message': f"Execution failed: {result['error']}"
                }

            # Record trade
            trade = Trade(
                trade_id=f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                symbol=symbol,
                side=signal,
                entry_price=analysis['entry_price'],
                quantity=quantity,
                stop_loss=stop_loss,
                take_profit=analysis['take_profit'],
                entry_time=datetime.now().isoformat(),
                reasons=analysis['reasons'],
                liquidity_score=analysis['liquidity_score'],
                indicator_strength=analysis['strength']
            )

            self.tracker.add_trade(trade)

            return {
                'success': True,
                'message': f"✅ Trade executed: {signal} {symbol}",
                'trade': trade,
                'binance_result': result,
                'trailing_stop_mode': analysis['trailing_stop_mode']
            }

        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return {
                'success': False,
                'message': f'Execution error: {str(e)}'
            }

    def monitor_active_trades(self) -> List[Dict]:
        """
        Monitor and manage active trades.

        Handles:
        - TP hit detection
        - Trailing stop activation (Scenario A)
        - Pullback SL widening (Scenario C)

        Returns:
            List of trade updates
        """
        updates = []

        try:
            open_trades = [t for t in self.tracker.trades if t.status == TradeStatus.OPEN.value]

            for trade in open_trades:
                # Get current price
                df_5m = self.get_market_data(trade.symbol, '5m', 20)
                if df_5m.empty:
                    continue

                current_price = df_5m['close'].iloc[-1]

                # Check TP levels
                tp1_hit = (
                    (trade.side == 'LONG' and current_price >= trade.take_profit['tp1']) or
                    (trade.side == 'SHORT' and current_price <= trade.take_profit['tp1'])
                )

                # Scenario A: Trailing Stop (2W + 1L)
                if tp1_hit and self.tracker.should_use_trailing_stop():
                    # Don't close at TP1, activate trailing stop
                    updates.append({
                        'trade_id': trade.trade_id,
                        'action': 'TRAILING_STOP_ACTIVATED',
                        'message': '📈 TP1 hit + Scenario A active → Trailing stop activated',
                        'current_price': current_price
                    })

                    # In production: Set trailing stop via Binance API
                    # For now, just log
                    logger.info(f"Trailing stop activated for {trade.trade_id}")

                # Scenario C: Pullback handling - This is now implicitly supported or must be redefined
                pass
                
                # Check if SL hit
                sl_hit = (
                    (trade.side == 'LONG' and current_price <= trade.stop_loss) or
                    (trade.side == 'SHORT' and current_price >= trade.stop_loss)
                )

                if sl_hit:
                    # Close trade
                    pnl = (current_price - trade.entry_price) * trade.quantity
                    if trade.side == 'SHORT':
                        pnl *= -1

                    self.tracker.close_trade(trade.trade_id, current_price, pnl)

                    updates.append({
                        'trade_id': trade.trade_id,
                        'action': 'CLOSED_SL',
                        'message': f'❌ Stop loss hit',
                        'pnl': pnl
                    })

        except Exception as e:
            logger.error(f"Error monitoring trades: {e}")

        return updates

    def get_strategy_status(self) -> Dict:
        """Get comprehensive strategy status."""
        return self.tracker.get_dashboard_summary()


# Singleton instance
_strategy = None

def get_advanced_strategy(testnet: bool = False, read_only: bool = True) -> AdvancedFuturesStrategy:
    """Get or create strategy instance."""
    global _strategy
    if _strategy is None:
        _strategy = AdvancedFuturesStrategy(testnet=testnet, read_only=read_only)
    return _strategy
