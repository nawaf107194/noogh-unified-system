#!/usr/bin/env python3
"""
Technical Analyzer - محلل فني متقدم

يحلل:
1. أنماط الشموع (Candlestick Patterns)
2. تقاطعات المؤشرات (MA, RSI, MACD)
3. مستويات الدعم/المقاومة
4. قوة الترند
5. Liquidity Zones
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TechnicalAnalyzer:
    """محلل فني متقدم"""
    
    def __init__(self):
        self.patterns = CandlestickPatterns()
        self.indicators = Indicators()
        self.support_resistance = SupportResistance()
    
    def analyze(self, df: pd.DataFrame, symbol: str = '') -> Dict:
        """تحليل شامل
        
        df columns: open, high, low, close, volume
        """
        if len(df) < 100:
            return {'error': 'Not enough data'}
        
        analysis = {
            'symbol': symbol,
            'timestamp': pd.Timestamp.now().isoformat(),
            'scores': {}
        }
        
        # 1. Candlestick Patterns (30 points)
        pattern_score, pattern_info = self.patterns.detect(df)
        analysis['candlestick_patterns'] = pattern_info
        analysis['scores']['patterns'] = pattern_score
        
        # 2. Indicator Signals (40 points)
        indicator_score, indicator_info = self.indicators.analyze(df)
        analysis['indicators'] = indicator_info
        analysis['scores']['indicators'] = indicator_score
        
        # 3. Support/Resistance (20 points)
        sr_score, sr_info = self.support_resistance.analyze(df)
        analysis['support_resistance'] = sr_info
        analysis['scores']['support_resistance'] = sr_score
        
        # 4. Trend Strength (10 points)
        trend_score, trend_info = self.analyze_trend_strength(df)
        analysis['trend'] = trend_info
        analysis['scores']['trend'] = trend_score
        
        # Total Technical Score (0-100)
        analysis['technical_score'] = sum(analysis['scores'].values())
        
        # Signal
        analysis['signal'] = self.generate_signal(analysis)
        
        return analysis
    
    def analyze_trend_strength(self, df: pd.DataFrame) -> Tuple[int, Dict]:
        """تحليل قوة الترند"""
        # ADX for trend strength
        adx = self.indicators.calculate_adx(df, period=14)
        current_adx = adx.iloc[-1]
        
        # EMA alignment
        ema_20 = df['close'].ewm(span=20).mean()
        ema_50 = df['close'].ewm(span=50).mean()
        ema_200 = df['close'].ewm(span=200).mean()
        
        ema_aligned = (
            (ema_20.iloc[-1] > ema_50.iloc[-1] > ema_200.iloc[-1]) or  # Uptrend
            (ema_20.iloc[-1] < ema_50.iloc[-1] < ema_200.iloc[-1])     # Downtrend
        )
        
        score = 0
        info = {'adx': current_adx}
        
        # ADX scoring
        if current_adx > 40:
            score += 7
            info['trend_strength'] = 'STRONG'
        elif current_adx > 25:
            score += 5
            info['trend_strength'] = 'MODERATE'
        else:
            score += 2
            info['trend_strength'] = 'WEAK'
        
        # EMA alignment bonus
        if ema_aligned:
            score += 3
            info['ema_alignment'] = 'ALIGNED'
        else:
            info['ema_alignment'] = 'MIXED'
        
        return score, info
    
    def generate_signal(self, analysis: Dict) -> Dict:
        """توليد إشارة تداول"""
        score = analysis['technical_score']
        
        # Direction from indicators
        indicators = analysis['indicators']
        direction = 'NEUTRAL'
        
        bullish_count = sum([
            indicators.get('rsi_signal') == 'BULLISH',
            indicators.get('macd_signal') == 'BULLISH',
            indicators.get('ma_signal') == 'BULLISH',
            analysis['candlestick_patterns'].get('bias') == 'BULLISH'
        ])
        
        bearish_count = sum([
            indicators.get('rsi_signal') == 'BEARISH',
            indicators.get('macd_signal') == 'BEARISH',
            indicators.get('ma_signal') == 'BEARISH',
            analysis['candlestick_patterns'].get('bias') == 'BEARISH'
        ])
        
        if bullish_count >= 3:
            direction = 'LONG'
        elif bearish_count >= 3:
            direction = 'SHORT'
        
        # Confidence based on score
        if score >= 80:
            confidence = 'HIGH'
        elif score >= 60:
            confidence = 'MEDIUM'
        else:
            confidence = 'LOW'
        
        return {
            'direction': direction,
            'confidence': confidence,
            'score': score,
            'should_enter': score >= 70 and direction != 'NEUTRAL'
        }


class CandlestickPatterns:
    """كاشف أنماط الشموع"""
    
    def detect(self, df: pd.DataFrame) -> Tuple[int, Dict]:
        """كشف الأنماط"""
        patterns_found = []
        score = 0
        
        # Last 3 candles
        last_3 = df.tail(3)
        
        # Bullish patterns
        if self.is_hammer(last_3.iloc[-1]):
            patterns_found.append('HAMMER')
            score += 10
        
        if self.is_engulfing_bullish(last_3.iloc[-2], last_3.iloc[-1]):
            patterns_found.append('BULLISH_ENGULFING')
            score += 15
        
        if self.is_morning_star(last_3):
            patterns_found.append('MORNING_STAR')
            score += 20
        
        # Bearish patterns
        if self.is_shooting_star(last_3.iloc[-1]):
            patterns_found.append('SHOOTING_STAR')
            score += 10
        
        if self.is_engulfing_bearish(last_3.iloc[-2], last_3.iloc[-1]):
            patterns_found.append('BEARISH_ENGULFING')
            score += 15
        
        if self.is_evening_star(last_3):
            patterns_found.append('EVENING_STAR')
            score += 20
        
        # Bias
        bullish_patterns = ['HAMMER', 'BULLISH_ENGULFING', 'MORNING_STAR']
        bearish_patterns = ['SHOOTING_STAR', 'BEARISH_ENGULFING', 'EVENING_STAR']
        
        bullish_count = sum(1 for p in patterns_found if p in bullish_patterns)
        bearish_count = sum(1 for p in patterns_found if p in bearish_patterns)
        
        bias = 'NEUTRAL'
        if bullish_count > bearish_count:
            bias = 'BULLISH'
        elif bearish_count > bullish_count:
            bias = 'BEARISH'
        
        # Cap score at 30
        score = min(score, 30)
        
        return score, {
            'patterns': patterns_found,
            'bias': bias,
            'count': len(patterns_found)
        }
    
    def is_hammer(self, candle: pd.Series) -> bool:
        """Hammer pattern"""
        body = abs(candle['close'] - candle['open'])
        lower_shadow = min(candle['open'], candle['close']) - candle['low']
        upper_shadow = candle['high'] - max(candle['open'], candle['close'])
        
        return (
            lower_shadow > body * 2 and
            upper_shadow < body * 0.3 and
            candle['close'] > candle['open']
        )
    
    def is_shooting_star(self, candle: pd.Series) -> bool:
        """Shooting Star pattern"""
        body = abs(candle['close'] - candle['open'])
        upper_shadow = candle['high'] - max(candle['open'], candle['close'])
        lower_shadow = min(candle['open'], candle['close']) - candle['low']
        
        return (
            upper_shadow > body * 2 and
            lower_shadow < body * 0.3 and
            candle['close'] < candle['open']
        )
    
    def is_engulfing_bullish(self, prev: pd.Series, curr: pd.Series) -> bool:
        """Bullish Engulfing"""
        return (
            prev['close'] < prev['open'] and  # Prev bearish
            curr['close'] > curr['open'] and  # Curr bullish
            curr['open'] < prev['close'] and
            curr['close'] > prev['open']
        )
    
    def is_engulfing_bearish(self, prev: pd.Series, curr: pd.Series) -> bool:
        """Bearish Engulfing"""
        return (
            prev['close'] > prev['open'] and  # Prev bullish
            curr['close'] < curr['open'] and  # Curr bearish
            curr['open'] > prev['close'] and
            curr['close'] < prev['open']
        )
    
    def is_morning_star(self, candles: pd.DataFrame) -> bool:
        """Morning Star (3-candle pattern)"""
        if len(candles) < 3:
            return False
        
        c1, c2, c3 = candles.iloc[-3], candles.iloc[-2], candles.iloc[-1]
        
        return (
            c1['close'] < c1['open'] and  # Bearish
            abs(c2['close'] - c2['open']) < abs(c1['close'] - c1['open']) * 0.3 and  # Small body
            c3['close'] > c3['open'] and  # Bullish
            c3['close'] > (c1['open'] + c1['close']) / 2  # Closes above midpoint
        )
    
    def is_evening_star(self, candles: pd.DataFrame) -> bool:
        """Evening Star (3-candle pattern)"""
        if len(candles) < 3:
            return False
        
        c1, c2, c3 = candles.iloc[-3], candles.iloc[-2], candles.iloc[-1]
        
        return (
            c1['close'] > c1['open'] and  # Bullish
            abs(c2['close'] - c2['open']) < abs(c1['close'] - c1['open']) * 0.3 and  # Small body
            c3['close'] < c3['open'] and  # Bearish
            c3['close'] < (c1['open'] + c1['close']) / 2  # Closes below midpoint
        )


class Indicators:
    """مؤشرات فنية"""
    
    def analyze(self, df: pd.DataFrame) -> Tuple[int, Dict]:
        """تحليل المؤشرات"""
        score = 0
        info = {}
        
        # 1. RSI (10 points)
        rsi = self.calculate_rsi(df)
        rsi_current = rsi.iloc[-1]
        info['rsi'] = rsi_current
        
        if rsi_current < 30:  # Oversold
            score += 10
            info['rsi_signal'] = 'BULLISH'
        elif rsi_current > 70:  # Overbought
            score += 10
            info['rsi_signal'] = 'BEARISH'
        elif 40 < rsi_current < 60:
            score += 5
            info['rsi_signal'] = 'NEUTRAL'
        else:
            info['rsi_signal'] = 'NEUTRAL'
        
        # 2. MACD (15 points)
        macd, signal, hist = self.calculate_macd(df)
        info['macd'] = {'macd': macd.iloc[-1], 'signal': signal.iloc[-1]}
        
        if hist.iloc[-1] > 0 and hist.iloc[-2] <= 0:  # Bullish crossover
            score += 15
            info['macd_signal'] = 'BULLISH'
        elif hist.iloc[-1] < 0 and hist.iloc[-2] >= 0:  # Bearish crossover
            score += 15
            info['macd_signal'] = 'BEARISH'
        elif hist.iloc[-1] > 0:
            score += 7
            info['macd_signal'] = 'BULLISH'
        else:
            info['macd_signal'] = 'BEARISH'
        
        # 3. Moving Average Crossovers (15 points)
        ma_20 = df['close'].rolling(20).mean()
        ma_50 = df['close'].rolling(50).mean()
        
        info['ma_20'] = ma_20.iloc[-1]
        info['ma_50'] = ma_50.iloc[-1]
        
        if ma_20.iloc[-1] > ma_50.iloc[-1] and ma_20.iloc[-2] <= ma_50.iloc[-2]:  # Golden cross
            score += 15
            info['ma_signal'] = 'BULLISH'
        elif ma_20.iloc[-1] < ma_50.iloc[-1] and ma_20.iloc[-2] >= ma_50.iloc[-2]:  # Death cross
            score += 15
            info['ma_signal'] = 'BEARISH'
        elif ma_20.iloc[-1] > ma_50.iloc[-1]:
            score += 7
            info['ma_signal'] = 'BULLISH'
        else:
            info['ma_signal'] = 'BEARISH'
        
        # Cap at 40
        score = min(score, 40)
        
        return score, info
    
    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD"""
        ema_12 = df['close'].ewm(span=12).mean()
        ema_26 = df['close'].ewm(span=26).mean()
        macd = ema_12 - ema_26
        signal = macd.ewm(span=9).mean()
        hist = macd - signal
        return macd, signal, hist
    
    def calculate_adx(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate ADX"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        plus_dm = high.diff()
        minus_dm = -low.diff()
        
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        tr = pd.concat([
            high - low,
            abs(high - close.shift()),
            abs(low - close.shift())
        ], axis=1).max(axis=1)
        
        atr = tr.rolling(period).mean()
        plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(period).mean()
        
        return adx


class SupportResistance:
    """تحليل الدعم والمقاومة"""
    
    def analyze(self, df: pd.DataFrame) -> Tuple[int, Dict]:
        """كشف مستويات S/R"""
        score = 0
        
        # Find pivot points
        support_levels = self.find_support(df)
        resistance_levels = self.find_resistance(df)
        
        current_price = df['close'].iloc[-1]
        
        # Distance to nearest support/resistance
        nearest_support = max([s for s in support_levels if s < current_price], default=0)
        nearest_resistance = min([r for r in resistance_levels if r > current_price], default=float('inf'))
        
        support_dist = (current_price - nearest_support) / current_price * 100 if nearest_support else 100
        resistance_dist = (nearest_resistance - current_price) / current_price * 100 if nearest_resistance != float('inf') else 100
        
        info = {
            'support_levels': support_levels[:3],
            'resistance_levels': resistance_levels[:3],
            'nearest_support': nearest_support,
            'nearest_resistance': nearest_resistance,
            'support_distance_pct': support_dist,
            'resistance_distance_pct': resistance_dist
        }
        
        # Scoring based on proximity
        if support_dist < 2:  # Very close to support (bounce opportunity)
            score += 20
            info['position'] = 'NEAR_SUPPORT'
        elif resistance_dist < 2:  # Very close to resistance (rejection risk)
            score += 20
            info['position'] = 'NEAR_RESISTANCE'
        elif 2 < support_dist < 5 and resistance_dist > 5:  # Good upside room
            score += 15
            info['position'] = 'GOOD_UPSIDE'
        elif resistance_dist < support_dist:  # More room to upside
            score += 10
            info['position'] = 'MODERATE'
        else:
            score += 5
            info['position'] = 'NEUTRAL'
        
        return score, info
    
    def find_support(self, df: pd.DataFrame, window: int = 20) -> List[float]:
        """إيجاد مستويات الدعم"""
        lows = df['low'].rolling(window, center=True).min()
        support = df[df['low'] == lows]['low'].unique()
        return sorted(support)[-5:]  # Top 5 support levels
    
    def find_resistance(self, df: pd.DataFrame, window: int = 20) -> List[float]:
        """إيجاد مستويات المقاومة"""
        highs = df['high'].rolling(window, center=True).max()
        resistance = df[df['high'] == highs]['high'].unique()
        return sorted(resistance)[:5]  # Top 5 resistance levels
