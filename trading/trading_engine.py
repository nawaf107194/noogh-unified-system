"""
Unified Trading Engine for NOOGH System
Integrates Intelligence Modules with Binance API for AI-powered trading.
"""

import sys
import os
sys.path.insert(0, '/home/noogh/projects/noogh_unified_system/src')

from typing import Dict, List, Optional
import logging
import pandas as pd

from trading.binance_integration import get_binance_manager
from trading.binance_futures import get_futures_manager

# Import intelligence modules
from unified_core.intelligence.funding_rate_filter import FundingRateFilter
from unified_core.intelligence.btc_correlation_guard import BtcCorrelationGuard

logger = logging.getLogger(__name__)


class TradingEngine:
    """
    Unified Trading Engine that combines:
    - Binance API (Spot & Futures)
    - Intelligence Modules (Guards, Filters, Signals)
    - Risk Management
    - Trade Execution
    """

    def __init__(self, testnet: bool = True, read_only: bool = True):
        """
        Initialize Trading Engine.

        Args:
            testnet: Use testnet (recommended)
            read_only: Read-only mode (no trading)
        """
        self.testnet = testnet
        self.read_only = read_only

        # Initialize Binance managers
        self.spot = get_binance_manager(testnet=testnet, read_only=read_only)
        self.futures = get_futures_manager(testnet=testnet, read_only=read_only, max_leverage=5)

        # Initialize intelligence modules
        self.funding_filter = FundingRateFilter()
        self.btc_guard = BtcCorrelationGuard()

        logger.info("✅ Trading Engine initialized")

    # ==========================================
    # DATA FETCHING (Integrated with Binance)
    # ==========================================

    def get_market_data(self, symbol: str, interval: str = '1h', limit: int = 100) -> pd.DataFrame:
        """
        Fetch market data from Binance.

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            interval: Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of candles

        Returns:
            DataFrame with OHLCV data
        """
        try:
            klines = self.spot.get_klines(symbol=symbol, interval=interval, limit=limit)
            df = pd.DataFrame(klines)
            return df
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return pd.DataFrame()

    def get_btc_correlation(self, symbol: str, period: int = 50) -> float:
        """
        Calculate correlation between BTC and another symbol.

        Args:
            symbol: Altcoin symbol (e.g., 'ETHUSDT')
            period: Number of candles for correlation

        Returns:
            Correlation coefficient (-1 to 1)
        """
        try:
            # Fetch BTC data
            btc_df = self.get_market_data('BTCUSDT', interval='15m', limit=period)
            if btc_df.empty:
                return 0.0

            # Fetch altcoin data
            alt_df = self.get_market_data(symbol, interval='15m', limit=period)
            if alt_df.empty:
                return 0.0

            # Calculate correlation
            correlation = btc_df['close'].corr(alt_df['close'])
            return correlation

        except Exception as e:
            logger.error(f"Error calculating correlation: {e}")
            return 0.0

    def get_funding_rate_signal(self, symbol: str = 'BTCUSDT') -> Dict:
        """
        Get funding rate signal for a symbol.

        Returns:
            Dict with funding rate and trading recommendation
        """
        try:
            funding = self.futures.get_funding_rate(symbol)

            if not funding:
                return {'error': 'Could not fetch funding rate'}

            rate = funding['funding_rate']

            # Analyze funding rate
            signal = {
                'symbol': symbol,
                'funding_rate': rate,
                'funding_rate_pct': rate * 100,
                'signal': 'NEUTRAL'
            }

            # High positive = too many longs (consider short)
            if rate > 0.001:  # 0.1%
                signal['signal'] = 'BEARISH'
                signal['reason'] = 'High funding rate - too many longs'
            # High negative = too many shorts (consider long)
            elif rate < -0.001:
                signal['signal'] = 'BULLISH'
                signal['reason'] = 'Negative funding rate - too many shorts'
            else:
                signal['reason'] = 'Normal funding rate'

            return signal

        except Exception as e:
            logger.error(f"Error getting funding rate signal: {e}")
            return {'error': str(e)}

    def get_btc_dominance_signal(self) -> Dict:
        """
        Analyze BTC dominance and altcoin safety.

        Returns:
            Signal for trading altcoins
        """
        try:
            # Get BTC price movement
            btc_df = self.get_market_data('BTCUSDT', interval='1h', limit=24)
            if btc_df.empty:
                return {'error': 'Could not fetch BTC data'}

            # Calculate BTC 24h change
            btc_change = (btc_df['close'].iloc[-1] - btc_df['close'].iloc[0]) / btc_df['close'].iloc[0] * 100

            # Get correlations for major altcoins
            altcoins = ['ETHUSDT', 'BNBUSDT', 'SOLUSDT']
            correlations = {}

            for alt in altcoins:
                corr = self.get_btc_correlation(alt)
                correlations[alt] = corr

            avg_correlation = sum(correlations.values()) / len(correlations)

            signal = {
                'btc_24h_change': btc_change,
                'avg_altcoin_correlation': avg_correlation,
                'correlations': correlations,
                'signal': 'NEUTRAL'
            }

            # High correlation + BTC dumping = don't trade alts
            if avg_correlation > 0.85 and btc_change < -2:
                signal['signal'] = 'AVOID_ALTS'
                signal['reason'] = 'High correlation + BTC dumping'
            # Low correlation = safe to trade alts
            elif avg_correlation < 0.7:
                signal['signal'] = 'SAFE_FOR_ALTS'
                signal['reason'] = 'Low correlation with BTC'
            # BTC pumping + high correlation = alts may follow
            elif avg_correlation > 0.8 and btc_change > 2:
                signal['signal'] = 'FOLLOW_BTC'
                signal['reason'] = 'High correlation + BTC pumping'

            return signal

        except Exception as e:
            logger.error(f"Error analyzing BTC dominance: {e}")
            return {'error': str(e)}

    def analyze_symbol(self, symbol: str) -> Dict:
        """
        Comprehensive analysis of a symbol.

        Args:
            symbol: Trading pair

        Returns:
            Complete analysis with signals
        """
        try:
            # Get current price
            price = self.spot.get_price(symbol)

            # Get 24h ticker
            ticker = self.spot.get_24h_ticker(symbol)

            # Get funding rate (if futures)
            funding_signal = self.get_funding_rate_signal(symbol)

            # Get BTC correlation
            correlation = self.get_btc_correlation(symbol) if symbol != 'BTCUSDT' else 1.0

            analysis = {
                'symbol': symbol,
                'price': price,
                '24h_change': ticker.get('change_percent', 0),
                '24h_volume': ticker.get('volume', 0),
                'btc_correlation': correlation,
                'funding_rate_signal': funding_signal,
                'overall_signal': 'NEUTRAL'
            }

            # Determine overall signal
            signals = []

            # Funding rate signal
            if funding_signal.get('signal') == 'BEARISH':
                signals.append('BEARISH')
            elif funding_signal.get('signal') == 'BULLISH':
                signals.append('BULLISH')

            # Correlation signal
            if correlation > 0.85:
                analysis['warning'] = 'High BTC correlation - risky for independent trades'

            # Price momentum
            if ticker.get('change_percent', 0) > 5:
                signals.append('BULLISH')
            elif ticker.get('change_percent', 0) < -5:
                signals.append('BEARISH')

            # Aggregate signals
            if signals.count('BULLISH') > signals.count('BEARISH'):
                analysis['overall_signal'] = 'BULLISH'
            elif signals.count('BEARISH') > signals.count('BULLISH'):
                analysis['overall_signal'] = 'BEARISH'

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing symbol: {e}")
            return {'error': str(e)}

    def get_portfolio_summary(self) -> Dict:
        """
        Get complete portfolio summary (Spot + Futures).

        Returns:
            Complete portfolio overview
        """
        try:
            # Spot balance
            spot_account = self.spot.get_account_info()
            spot_balances = spot_account.get('balances', [])

            # Futures balance
            futures_account = self.futures.get_futures_account()
            futures_positions = self.futures.get_positions()

            # Calculate totals
            spot_total = sum(b['total'] * self.spot.get_price(f"{b['asset']}USDT")
                           for b in spot_balances
                           if b['asset'] != 'USDT')

            spot_usdt = next((b['total'] for b in spot_balances if b['asset'] == 'USDT'), 0)

            futures_total = futures_account.get('total_wallet_balance', 0)
            futures_pnl = futures_account.get('total_unrealized_pnl', 0)

            summary = {
                'spot': {
                    'total_value_usdt': spot_total + spot_usdt,
                    'assets_count': len([b for b in spot_balances if b['total'] > 0])
                },
                'futures': {
                    'total_balance': futures_total,
                    'unrealized_pnl': futures_pnl,
                    'open_positions': len(futures_positions)
                },
                'grand_total': spot_total + spot_usdt + futures_total + futures_pnl
            }

            return summary

        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return {'error': str(e)}


# Singleton instance
_trading_engine = None

def get_trading_engine(testnet: bool = True, read_only: bool = True) -> TradingEngine:
    """Get or create Trading Engine instance."""
    global _trading_engine
    if _trading_engine is None:
        _trading_engine = TradingEngine(testnet=testnet, read_only=read_only)
    return _trading_engine
