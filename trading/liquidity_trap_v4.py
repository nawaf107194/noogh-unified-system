# Liquidity Trap V4 Signal Engine

import numpy as np
import pandas as pd
from typing import Dict, Tuple

from noogh.trading.technical_indicators import TechnicalIndicatorsV2

class LiquidityTrapV4:
    '''
    Enhanced liquidity trap detection with:
    - Volume Profile analysis
    - Order flow imbalance
    - Multi-timeframe confirmation
    - Smart money concepts
    '''

    @staticmethod
    def generate_entry_signal(df_1h: pd.DataFrame, df_5m: pd.DataFrame) -> Dict:
        '''Generate advanced liquidity trap signal'''
        
        # 1. Volume Profile POC/VAH/VAL
        vp = LiquidityTrapV4._calculate_volume_profile(df_5m)
        poc = vp['poc']
        vah = vp['vah']
        val = vp['val']

        # 2. Order Flow Imbalance (5m)
        ofi = LiquidityTrapV4._order_flow_imbalance(df_5m)

        # 3. Liquidity Sweep Detection
        sweep_long = LiquidityTrapV4._detect_liquidity_sweep(df_5m, direction='long')
        sweep_short = LiquidityTrapV4._detect_liquidity_sweep(df_5m, direction='short')

        # 4. Multi-timeframe alignment
        macro_trend = TechnicalIndicatorsV2.macro_trend(df_1h)
        micro_momentum = TechnicalIndicatorsV2.rsi(df_5m, 14)

        # Signal Logic
        signal = 'NEUTRAL'
        strength = 0
        reasons = []

        if sweep_long and ofi > 0.6 and micro_momentum < 35 and macro_trend == 'bullish':
            signal = 'LONG'
            strength = min(100, 50 + ofi*30 + (35-micro_momentum)*1.5)
            reasons = ['Liquidity sweep long', 'OFI bullish', 'Oversold RSI', 'Macro bullish']
        
        elif sweep_short and ofi < -0.6 and micro_momentum > 65 and macro_trend == 'bearish':
            signal = 'SHORT'
            strength = min(100, 50 + abs(ofi)*30 + (micro_momentum-65)*1.5)
            reasons = ['Liquidity sweep short', 'OFI bearish', 'Overbought RSI', 'Macro bearish']

        # Risk targets (dynamic based on VP)
        atr = TechnicalIndicatorsV2.atr(df_5m, 14)
        stop_loss_long = val - atr * 0.5
        tp1_long = poc + atr * 1.5
        tp2_long = vah + atr * 0.5

        return {
            'signal': signal,
            'strength': strength,
            'poc': poc,
            'vah': vah,
            'val': val,
            'ofi': ofi,
            'stop_loss': stop_loss_long if signal == 'LONG' else None,
            'take_profits': {
                'tp1': tp1_long,
                'tp2': tp2_long,
                'rrr': 2.2  # Dynamic RRR
            },
            'macro_trend': macro_trend,
            'reasons': reasons,
            'liquidity_score': strength
        }

    @staticmethod
    def _calculate_volume_profile(df: pd.DataFrame, bins: int = 50) -> Dict:
        '''Calculate Volume Profile POC/VAH/VAL'''
        price_range = df['high'].max() - df['low'].min()
        bin_size = price_range / bins
        
        volume_profile = np.zeros(bins)
        price_bins = np.arange(df['low'].min(), df['high'].max() + bin_size, bin_size)
        
        for _, row in df.iterrows():
            bin_idx = np.digitize(row['close'], price_bins) - 1
            if 0 <= bin_idx < bins:
                volume_profile[bin_idx] += row['volume']
        
        poc_idx = np.argmax(volume_profile)
        poc_price = price_bins[poc_idx]
        vah = price_bins[np.argmax(volume_profile > np.max(volume_profile)*0.7)]
        val = price_bins[np.argmax(volume_profile[::-1] > np.max(volume_profile)*0.7)]
        
        return {'poc': poc_price, 'vah': vah, 'val': val}

    @staticmethod
    def _order_flow_imbalance(df: pd.DataFrame) -> float:
        '''Calculate OFI score (-1 to 1)'''
        # Simplified OFI using volume delta
        df['volume_delta'] = df['close'] - df['open']
        df['buy_volume'] = np.where(df['volume_delta'] > 0, df['volume'], 0)
        df['sell_volume'] = np.where(df['volume_delta'] < 0, df['volume'], 0)
        
        recent_buy = df['buy_volume'].tail(10).sum()
        recent_sell = df['sell_volume'].tail(10).sum()
        
        return (recent_buy - recent_sell) / (recent_buy + recent_sell + 1e-8)

    @staticmethod
    def _detect_liquidity_sweep(df: pd.DataFrame, direction: str = 'long') -> bool:
        '''Detect liquidity sweep below/above recent lows/highs'''
        if direction == 'long':
            recent_low = df['low'].tail(20).min()
            sweep = df['low'].iloc[-2] < recent_low and df['close'].iloc[-1] > recent_low
        else:
            recent_high = df['high'].tail(20).max()
            sweep = df['high'].iloc[-2] > recent_high and df['close'].iloc[-1] < recent_high
        return sweep
