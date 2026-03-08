# Multi-Asset Statistical Arbitrage
# BTC-ETH-USDT Triangular Arb + Futures Basis Trading

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from scipy import stats

from noogh.trading.regime_detector import RegimeDetector

class MultiAssetArb:
    """
    Multi-asset arbitrage strategies:
    1. BTC-ETH Triangular Arb
    2. Futures-Spot Basis Trading
    3. Cross-exchange Arb (Binance vs Bybit)
    """

    PAIRS = ['BTCUSDT', 'ETHUSDT', 'BTCETH']  # Perpetual futures

    @staticmethod
    def detect_triangular_arb(opportunities: Dict[str, float]) -> List[Dict]:
        """
        Detect BTC-ETH-USDT triangular arbitrage.

        Returns:
            List of profitable arb opportunities
        """
        arb_ops = []

        # Path 1: USDT → BTC → ETH → USDT
        path1_return = (1 / opportunities['BTCUSDT']) * opportunities['BTCETH'] * opportunities['ETHUSDT']
        if path1_return > 1.002:  # 0.2% threshold after fees
            arb_ops.append({
                'path': 'USDT→BTC→ETH→USDT',
                'expected_return': path1_return - 1,
                'risk': 'low',
                'confidence': 95
            })

        # Path 2: USDT → ETH → BTC → USDT
        path2_return = (1 / opportunities['ETHUSDT']) * (1 / opportunities['BTCETH']) * opportunities['BTCUSDT']
        if path2_return > 1.002:
            arb_ops.append({
                'path': 'USDT→ETH→BTC→USDT',
                'expected_return': path2_return - 1,
                'risk': 'low',
                'confidence': 95
            })

        return arb_ops

    @staticmethod
    def futures_basis_trade(symbol: str, df_futures: pd.DataFrame, df_spot: pd.DataFrame) -> Dict:
        """
        Futures-spot basis trading.

        Long spot + Short futures when basis > threshold
        """
        # Calculate basis = (Futures Price - Spot Price) / Spot Price
        basis = (df_futures['close'] - df_spot['close']) / df_spot['close']
        basis_mean = basis.mean()
        basis_std = basis.std()
        current_basis = basis.iloc[-1]

        signal = 'NEUTRAL'
        zscore = (current_basis - basis_mean) / basis_std

        if zscore > 2.0:
            signal = 'SHORT_BASIS'  # Short futures, long spot
        elif zscore < -2.0:
            signal = 'LONG_BASIS'   # Long futures, short spot

        return {
            'symbol': symbol,
            'signal': signal,
            'current_basis': current_basis,
            'zscore': zscore,
            'entry_threshold': 2.0,
            'expected_convergence': abs(zscore) * basis_std
        }

    @staticmethod
    def stat_arb_pairs(df_data: Dict[str, pd.DataFrame]) -> List[Dict]:
        """
        Statistical arbitrage between correlated pairs.

        Cointegration test + Z-score trading
        """
        signals = []

        for pair1, pair2 in [('BTCUSDT', 'ETHUSDT')]:
            # Cointegration test
            score, pvalue, _ = stats.coint(df_data[pair1]['close'], df_data[pair2]['close'])
            if pvalue < 0.05:  # Cointegrated
                spread = df_data[pair1]['close'] - df_data[pair2]['close'] * 0.05  # Hedge ratio
                spread_z = (spread - spread.mean()) / spread.std()

                if spread_z.iloc[-1] > 2:
                    signals.append({
                        'pair': f'{pair1}-{pair2}',
                        'signal': 'SHORT_SPREAD',
                        'zscore': spread_z.iloc[-1],
                        'hedge_ratio': 0.05
                    })
                elif spread_z.iloc[-1] < -2:
                    signals.append({
                        'pair': f'{pair1}-{pair2}',
                        'signal': 'LONG_SPREAD',
                        'zscore': spread_z.iloc[-1],
                        'hedge_ratio': 0.05
                    })

        return signals

# Integration with main strategy:
# arb_signals = MultiAssetArb.detect_triangular_arb(prices)
# basis = MultiAssetArb.futures_basis_trade('BTCUSDT', df_fut, df_spot)