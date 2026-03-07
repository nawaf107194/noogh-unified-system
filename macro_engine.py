#!/usr/bin/env python3
"""
NOOGH Macro Trading Engine
============================
Bridgewater-style macro regime detection for crypto allocation.

Framework:
- 15 macro indicators from public APIs (FRED, CoinGecko)
- Growth/Inflation 2×2 regime matrix
- Crypto-specific asset behavior map in each regime
- All-Weather baseline + tactical overlays
- Correlation regime monitoring
- Risk-on/Risk-off scoring

Usage:
    python3 macro_engine.py
    python3 macro_engine.py --history
"""

import sys
import json
import time
import argparse
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any

import numpy as np
import requests

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')


# ═══════════════════════════════════════════════════════════════
# Section 1: Macro Economic Machine (Dalio Framework)
# ═══════════════════════════════════════════════════════════════

"""
Bridgewater's "Economic Machine" has 2 key dimensions:

                  GROWTH ↑
            ┌──────┬──────────┐
            │      │          │
 INFLATION  │  II  │    I     │   I:  Rising Growth + Rising Inflation  = GOLDILOCKS early → OVERHEAT late
    ↑       │      │          │   II: Rising Growth + Falling Inflation = GOLDILOCKS (best for crypto)
            ├──────┼──────────┤   III: Falling Growth + Falling Inflation = DEFLATION/RECESSION
 INFLATION  │ III  │   IV     │   IV: Falling Growth + Rising Inflation = STAGFLATION (worst)
    ↓       │      │          │
            └──────┴──────────┘
                  GROWTH ↓
"""

@dataclass
class MacroRegime:
    name: str
    growth: str         # 'RISING' or 'FALLING'
    inflation: str      # 'RISING' or 'FALLING'
    
    # Expected crypto behavior in this regime
    crypto_bias: str    # 'BULLISH', 'BEARISH', 'NEUTRAL'
    confidence: float   # 0-1
    
    # Allocation weights
    btc_weight: float
    alt_weight: float
    stablecoin_weight: float
    leverage_cap: int

REGIMES = {
    'GOLDILOCKS': MacroRegime(
        name='GOLDILOCKS',
        growth='RISING', inflation='FALLING',
        crypto_bias='BULLISH', confidence=0.8,
        btc_weight=0.40, alt_weight=0.40, stablecoin_weight=0.20,
        leverage_cap=15
    ),
    'OVERHEAT': MacroRegime(
        name='OVERHEAT', 
        growth='RISING', inflation='RISING',
        crypto_bias='NEUTRAL', confidence=0.5,
        btc_weight=0.35, alt_weight=0.25, stablecoin_weight=0.40,
        leverage_cap=10
    ),
    'DEFLATION': MacroRegime(
        name='DEFLATION',
        growth='FALLING', inflation='FALLING',
        crypto_bias='BEARISH', confidence=0.7,
        btc_weight=0.20, alt_weight=0.10, stablecoin_weight=0.70,
        leverage_cap=5
    ),
    'STAGFLATION': MacroRegime(
        name='STAGFLATION',
        growth='FALLING', inflation='RISING',
        crypto_bias='BEARISH', confidence=0.9,
        btc_weight=0.15, alt_weight=0.05, stablecoin_weight=0.80,
        leverage_cap=3
    ),
}


# ═══════════════════════════════════════════════════════════════
# Section 2: Macro Indicator Dashboard (15 Signals)
# ═══════════════════════════════════════════════════════════════

class MacroDataFetcher:
    """Fetch macro indicators from public APIs."""
    
    def __init__(self):
        self.cache: Dict[str, Any] = {}
    
    def fetch_all(self) -> Dict[str, Any]:
        """Fetch all available macro indicators."""
        indicators = {}
        
        # ── Crypto-Native Indicators (CoinGecko) ──
        indicators.update(self._fetch_crypto_macro())
        
        # ── Market-Based Indicators (Binance) ──
        indicators.update(self._fetch_market_indicators())
        
        # ── Fear & Greed ──
        indicators.update(self._fetch_fear_greed())
        
        return indicators
    
    def _fetch_crypto_macro(self) -> Dict:
        """BTC dominance, USDT dominance, Total market cap."""
        result = {}
        try:
            r = requests.get('https://api.coingecko.com/api/v3/global', timeout=10)
            if r.status_code == 200:
                data = r.json().get('data', {})
                mc = data.get('total_market_cap', {})
                
                result['btc_dominance'] = data.get('market_cap_percentage', {}).get('btc', 0)
                result['eth_dominance'] = data.get('market_cap_percentage', {}).get('eth', 0)
                result['total_market_cap_usd'] = mc.get('usd', 0) / 1e12  # in trillions
                result['market_cap_change_24h'] = data.get('market_cap_change_percentage_24h_usd', 0)
                
                # USDT dominance (proxy for risk-off)
                usdt_cap = 0
                try:
                    r2 = requests.get('https://api.coingecko.com/api/v3/coins/tether', timeout=5)
                    if r2.status_code == 200:
                        usdt_cap = r2.json().get('market_data', {}).get('market_cap', {}).get('usd', 0)
                        total = mc.get('usd', 1)
                        result['usdt_dominance'] = usdt_cap / total * 100 if total > 0 else 0
                except:
                    result['usdt_dominance'] = 0
        except Exception as e:
            logger.warning(f"CoinGecko error: {e}")
        
        return result
    
    def _fetch_market_indicators(self) -> Dict:
        """BTC price momentum, volatility, correlations from Binance."""
        result = {}
        try:
            BASE = "https://api.binance.com/api/v3"
            
            # BTC 30-day momentum
            r = requests.get(f"{BASE}/klines", params={
                'symbol': 'BTCUSDT', 'interval': '1d', 'limit': 30
            }, timeout=10)
            if r.status_code == 200:
                klines = r.json()
                closes = [float(k[4]) for k in klines]
                if len(closes) >= 30:
                    result['btc_30d_return'] = (closes[-1] / closes[0] - 1) * 100
                    result['btc_7d_return'] = (closes[-1] / closes[-7] - 1) * 100 if len(closes) >= 7 else 0
                    result['btc_price'] = closes[-1]
                    
                    # Volatility (30d annualized)
                    rets = np.diff(closes) / closes[:-1]
                    result['btc_30d_vol'] = np.std(rets) * np.sqrt(365) * 100
                    
                    # Trend: above/below 20-day SMA
                    sma20 = np.mean(closes[-20:])
                    result['btc_above_sma20'] = closes[-1] > sma20
                    result['btc_sma20_dist'] = (closes[-1] / sma20 - 1) * 100
                    
            # ETH/BTC ratio (risk appetite)
            r2 = requests.get(f"{BASE}/ticker/24hr", params={'symbol': 'ETHBTC'}, timeout=5)
            if r2.status_code == 200:
                result['eth_btc_ratio'] = float(r2.json().get('lastPrice', 0))
                result['eth_btc_24h_change'] = float(r2.json().get('priceChangePercent', 0))
            
            # SOL/BTC (alt sentiment)
            r3 = requests.get(f"{BASE}/klines", params={'symbol': 'SOLUSDT', 'interval': '1d', 'limit': 7}, timeout=5)
            if r3.status_code == 200:
                sol_closes = [float(k[4]) for k in r3.json()]
                if len(sol_closes) >= 7:
                    result['sol_7d_return'] = (sol_closes[-1] / sol_closes[0] - 1) * 100
                    
        except Exception as e:
            logger.warning(f"Binance error: {e}")
        
        return result
    
    def _fetch_fear_greed(self) -> Dict:
        """Alternative.me Fear & Greed Index."""
        try:
            r = requests.get('https://api.alternative.me/fng/?limit=1', timeout=5)
            if r.status_code == 200:
                data = r.json().get('data', [{}])[0]
                return {
                    'fear_greed': int(data.get('value', 50)),
                    'fear_greed_label': data.get('value_classification', 'Neutral'),
                }
        except:
            pass
        return {'fear_greed': 50, 'fear_greed_label': 'Neutral'}


# ═══════════════════════════════════════════════════════════════
# Section 3: Regime Detection Engine
# ═══════════════════════════════════════════════════════════════

class RegimeDetector:
    """
    Classify current macro regime using the Growth/Inflation matrix.
    
    Crypto-adapted:
    - Growth proxy: BTC momentum + total market cap change + alt performance
    - Inflation proxy: USDT dominance (inverse) + BTC dominance (flight to quality)
    """
    
    def detect(self, indicators: Dict) -> Tuple[str, MacroRegime, Dict]:
        """
        Returns (regime_name, MacroRegime, details).
        """
        # ── Growth Score (-1 to +1) ──
        growth_signals = []
        
        # BTC 30d return: positive = growth
        btc_30d = indicators.get('btc_30d_return', 0)
        growth_signals.append(('BTC 30d Return', np.clip(btc_30d / 20, -1, 1)))
        
        # BTC 7d return: recent momentum
        btc_7d = indicators.get('btc_7d_return', 0)
        growth_signals.append(('BTC 7d Return', np.clip(btc_7d / 10, -1, 1)))
        
        # Market cap change: positive = growth
        mc_change = indicators.get('market_cap_change_24h', 0)
        growth_signals.append(('Market Cap 24h', np.clip(mc_change / 5, -1, 1)))
        
        # ETH/BTC change: positive = risk on (growth)
        eth_btc = indicators.get('eth_btc_24h_change', 0)
        growth_signals.append(('ETH/BTC 24h', np.clip(eth_btc / 5, -1, 1)))
        
        # BTC above SMA: trend
        above_sma = indicators.get('btc_above_sma20', False)
        growth_signals.append(('BTC vs SMA20', 1.0 if above_sma else -1.0))
        
        # Fear & Greed > 50 = growth optimism
        fg = indicators.get('fear_greed', 50)
        growth_signals.append(('Fear/Greed', np.clip((fg - 50) / 25, -1, 1)))
        
        growth_score = np.mean([s[1] for s in growth_signals])
        
        # ── Inflation Score (-1 to +1) ──
        # In crypto context: "inflation" = risk premium / heating
        inflation_signals = []
        
        # USDT dominance HIGH = deflation (money in stables), LOW = inflation (risk on)
        usdt_d = indicators.get('usdt_dominance', 7)
        inflation_signals.append(('USDT.D (inverse)', np.clip((7 - usdt_d) / 3, -1, 1)))
        
        # BTC dominance HIGH = flight to quality (deflation), LOW = alt season (inflation/heat)
        btc_d = indicators.get('btc_dominance', 55)
        inflation_signals.append(('BTC.D (inverse)', np.clip((55 - btc_d) / 10, -1, 1)))
        
        # High volatility = chaotic (stagflation-like)
        vol = indicators.get('btc_30d_vol', 50)
        inflation_signals.append(('Volatility', np.clip((vol - 50) / 30, -1, 1)))
        
        # SOL outperforming BTC = speculation (heating)
        sol_7d = indicators.get('sol_7d_return', 0)
        btc_7d_val = indicators.get('btc_7d_return', 0)
        sol_alpha = sol_7d - btc_7d_val if btc_7d_val != 0 else 0
        inflation_signals.append(('SOL Alpha vs BTC', np.clip(sol_alpha / 10, -1, 1)))
        
        inflation_score = np.mean([s[1] for s in inflation_signals])
        
        # ── Classify Regime ──
        if growth_score > 0 and inflation_score <= 0:
            regime_name = 'GOLDILOCKS'
        elif growth_score > 0 and inflation_score > 0:
            regime_name = 'OVERHEAT'
        elif growth_score <= 0 and inflation_score <= 0:
            regime_name = 'DEFLATION'
        else:
            regime_name = 'STAGFLATION'
        
        regime = REGIMES[regime_name]
        
        # Confidence based on signal agreement
        growth_agreement = abs(growth_score)
        inflation_agreement = abs(inflation_score)
        confidence = (growth_agreement + inflation_agreement) / 2
        
        details = {
            'growth_score': round(growth_score, 3),
            'inflation_score': round(inflation_score, 3),
            'confidence': round(confidence, 3),
            'growth_signals': [(n, round(v, 3)) for n, v in growth_signals],
            'inflation_signals': [(n, round(v, 3)) for n, v in inflation_signals],
        }
        
        return regime_name, regime, details


# ═══════════════════════════════════════════════════════════════
# Section 4: Risk-On/Risk-Off Scoring
# ═══════════════════════════════════════════════════════════════

class RiskAppetiteScorer:
    """
    Composite risk-on/risk-off score for crypto.
    
    Risk-On signals: rising BTC, falling USDT.D, low BTC.D, high F&G
    Risk-Off signals: falling BTC, rising USDT.D, high BTC.D, low F&G
    """
    
    def score(self, indicators: Dict) -> Dict:
        signals = []
        
        # BTC 7d momentum
        btc_7d = indicators.get('btc_7d_return', 0)
        signals.append(('BTC 7d', np.clip(btc_7d / 10, -1, 1), 0.25))
        
        # Fear & Greed
        fg = indicators.get('fear_greed', 50)
        signals.append(('Fear/Greed', np.clip((fg - 50) / 25, -1, 1), 0.20))
        
        # USDT dominance (inverse)
        usdt = indicators.get('usdt_dominance', 7)
        signals.append(('USDT.D', np.clip((7 - usdt) / 3, -1, 1), 0.20))
        
        # BTC above SMA20
        above = indicators.get('btc_above_sma20', False)
        signals.append(('BTC Trend', 1.0 if above else -1.0, 0.15))
        
        # ETH/BTC change
        eth_btc = indicators.get('eth_btc_24h_change', 0)
        signals.append(('ETH/BTC', np.clip(eth_btc / 5, -1, 1), 0.10))
        
        # Volatility (high vol = uncertainty)
        vol = indicators.get('btc_30d_vol', 50)
        signals.append(('Volatility', np.clip((60 - vol) / 30, -1, 1), 0.10))
        
        composite = sum(s[1] * s[2] for s in signals)
        
        if composite > 0.3:
            mode = '🟢 RISK-ON'
        elif composite < -0.3:
            mode = '🔴 RISK-OFF'
        else:
            mode = '🟡 NEUTRAL'
        
        return {
            'score': round(composite, 3),
            'mode': mode,
            'signals': [(n, round(v, 3), w) for n, v, w in signals],
        }


# ═══════════════════════════════════════════════════════════════
# Section 5: Portfolio Allocator
# ═══════════════════════════════════════════════════════════════

class CryptoAllocator:
    """
    All-Weather baseline + tactical overlay for crypto.
    """
    
    # Baseline All-Weather (designed for any regime)
    ALL_WEATHER = {
        'BTC': 0.30,    # Digital gold
        'ETH': 0.25,    # Smart contract platform
        'SOL': 0.10,    # High-beta alt
        'BNB': 0.05,    # Exchange token
        'STABLES': 0.30, # Cash/USDT
    }
    
    def allocate(self, regime: MacroRegime, risk_appetite: Dict, 
                 indicators: Dict) -> Dict:
        """Generate tactical allocation based on regime and risk."""
        
        # Start with All-Weather baseline
        alloc = self.ALL_WEATHER.copy()
        
        risk_score = risk_appetite['score']
        
        # ── Tactical Overlay ──
        if regime.name == 'GOLDILOCKS':
            # Increase risk: more alts, less stables
            alloc['BTC'] += 0.10
            alloc['ETH'] += 0.10
            alloc['SOL'] += 0.05
            alloc['STABLES'] -= 0.25
            
        elif regime.name == 'OVERHEAT':
            # Moderate: BTC safe, reduce alts slightly
            alloc['BTC'] += 0.05
            alloc['STABLES'] -= 0.05
            
        elif regime.name == 'DEFLATION':
            # Defensive: reduce all crypto, increase stables
            alloc['BTC'] -= 0.10
            alloc['ETH'] -= 0.10
            alloc['SOL'] -= 0.05
            alloc['STABLES'] += 0.25
            
        elif regime.name == 'STAGFLATION':
            # Maximum defense
            alloc['BTC'] -= 0.15
            alloc['ETH'] -= 0.15
            alloc['SOL'] -= 0.08
            alloc['STABLES'] += 0.38
        
        # Risk appetite modifier
        if risk_score < -0.5:
            # Extra defensive
            shift = 0.10
            alloc['STABLES'] += shift
            alloc['SOL'] -= shift * 0.5
            alloc['ETH'] -= shift * 0.5
        elif risk_score > 0.5:
            # Extra aggressive
            shift = 0.05
            alloc['SOL'] += shift
            alloc['STABLES'] -= shift
        
        # Floor/cap
        for k in alloc:
            alloc[k] = max(0.0, min(1.0, alloc[k]))
        
        # Normalize to 100%
        total = sum(alloc.values())
        if total > 0:
            alloc = {k: round(v / total, 3) for k, v in alloc.items()}
        
        # Leverage cap from regime
        leverage = regime.leverage_cap
        
        # Trading direction from regime
        direction = 'LONG' if regime.crypto_bias == 'BULLISH' else 'SHORT' if regime.crypto_bias == 'BEARISH' else 'NEUTRAL'
        
        return {
            'allocation': alloc,
            'direction': direction,
            'leverage_cap': leverage,
            'regime': regime.name,
        }


# ═══════════════════════════════════════════════════════════════
# Section 6: Correlation Regime Monitor
# ═══════════════════════════════════════════════════════════════

class CorrelationMonitor:
    """Monitor how crypto correlations change during stress."""
    
    def analyze(self, indicators: Dict) -> Dict:
        """Assess correlation regime."""
        vol = indicators.get('btc_30d_vol', 50)
        btc_d = indicators.get('btc_dominance', 55)
        fg = indicators.get('fear_greed', 50)
        
        # During stress: correlations spike to 1 (everything falls together)
        stress_score = 0
        if vol > 70: stress_score += 1
        if btc_d > 60: stress_score += 1  # Flight to BTC
        if fg < 25: stress_score += 1       # Extreme fear
        
        if stress_score >= 2:
            regime = '🔴 CRISIS — All correlations → 1'
            action = 'Reduce ALL positions. Only stables.'
        elif stress_score == 1:
            regime = '🟡 ELEVATED — Correlations rising'
            action = 'Reduce alts, increase BTC weight.'
        else:
            regime = '🟢 NORMAL — Diversification works'
            action = 'Trade normally. Pairs trading viable.'
        
        return {
            'regime': regime,
            'stress_score': stress_score,
            'action': action,
            'btc_vol_30d': round(vol, 1),
        }


# ═══════════════════════════════════════════════════════════════
# Section 7: Report
# ═══════════════════════════════════════════════════════════════

def generate_report(indicators: Dict, regime_name: str, regime: MacroRegime,
                    regime_details: Dict, risk: Dict, allocation: Dict,
                    correlation: Dict):
    
    print("\n" + "=" * 80)
    print(f"  NOOGH MACRO TRADING DASHBOARD")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')} | Bridgewater Framework")
    print("=" * 80)
    
    # Macro Indicators
    print(f"\n📊 MACRO INDICATORS")
    print(f"  {'BTC Price:':<25} ${indicators.get('btc_price', 0):>10,.0f}")
    print(f"  {'BTC 7d Return:':<25} {indicators.get('btc_7d_return', 0):>9.1f}%")
    print(f"  {'BTC 30d Return:':<25} {indicators.get('btc_30d_return', 0):>9.1f}%")
    print(f"  {'BTC 30d Volatility:':<25} {indicators.get('btc_30d_vol', 0):>9.1f}%")
    print(f"  {'BTC vs SMA20:':<25} {'✅ Above' if indicators.get('btc_above_sma20') else '❌ Below':>9}")
    print(f"  {'BTC Dominance:':<25} {indicators.get('btc_dominance', 0):>9.1f}%")
    print(f"  {'ETH Dominance:':<25} {indicators.get('eth_dominance', 0):>9.1f}%")
    print(f"  {'USDT Dominance:':<25} {indicators.get('usdt_dominance', 0):>9.2f}%")
    print(f"  {'Total Market Cap:':<25} ${indicators.get('total_market_cap_usd', 0):>8.2f}T")
    print(f"  {'Fear & Greed:':<25} {indicators.get('fear_greed', 0):>5} ({indicators.get('fear_greed_label', '')})")
    print(f"  {'ETH/BTC Ratio:':<25} {indicators.get('eth_btc_ratio', 0):>9.6f}")
    
    # Growth/Inflation Matrix
    gs = regime_details['growth_score']
    inf_s = regime_details['inflation_score']
    
    print(f"\n📐 GROWTH/INFLATION MATRIX")
    print(f"  Growth Score:    {gs:+.3f} ({'RISING ↑' if gs > 0 else 'FALLING ↓'})")
    for name, val in regime_details['growth_signals']:
        marker = "▲" if val > 0 else "▼"
        print(f"    {marker} {name:<20} {val:+.3f}")
    
    print(f"  Inflation Score: {inf_s:+.3f} ({'RISING ↑' if inf_s > 0 else 'FALLING ↓'})")
    for name, val in regime_details['inflation_signals']:
        marker = "▲" if val > 0 else "▼"
        print(f"    {marker} {name:<20} {val:+.3f}")
    
    # Regime
    regime_emoji = {'GOLDILOCKS': '🌟', 'OVERHEAT': '🔥', 'DEFLATION': '❄️', 'STAGFLATION': '💀'}
    print(f"\n{'─' * 80}")
    print(f"  {regime_emoji.get(regime_name, '?')} REGIME: {regime_name}")
    print(f"{'─' * 80}")
    print(f"  Growth: {regime.growth} | Inflation: {regime.inflation}")
    print(f"  Crypto Bias: {regime.crypto_bias}")
    print(f"  Confidence: {regime_details['confidence']:.0%}")
    print(f"  Max Leverage: {regime.leverage_cap}x")
    
    # Risk Appetite
    print(f"\n🎯 RISK APPETITE: {risk['mode']} (score: {risk['score']:+.3f})")
    for name, val, weight in risk['signals']:
        marker = "🟢" if val > 0.3 else "🔴" if val < -0.3 else "⚪"
        print(f"    {marker} {name:<15} {val:+.3f} (w={weight:.0%})")
    
    # Allocation
    alloc = allocation['allocation']
    print(f"\n💼 PORTFOLIO ALLOCATION ({allocation['regime']})")
    print(f"  Direction: {allocation['direction']} | Max Leverage: {allocation['leverage_cap']}x")
    for asset, weight in sorted(alloc.items(), key=lambda x: -x[1]):
        bar = "█" * int(weight * 40)
        print(f"  {asset:<10} {weight*100:>5.1f}%  {bar}")
    
    # Correlation
    print(f"\n🔗 CORRELATION REGIME")
    print(f"  {correlation['regime']}")
    print(f"  Action: {correlation['action']}")
    
    # Trading Directive
    print(f"\n{'═' * 80}")
    print(f"  🎯 TRADING DIRECTIVE")
    print(f"{'═' * 80}")
    
    if regime_name == 'GOLDILOCKS':
        print(f"  ✅ GO LONG — Best regime for crypto")
        print(f"  • Open LONG positions with up to {regime.leverage_cap}x leverage")
        print(f"  • Focus: ETH, SOL (high beta)")
        print(f"  • Risk: 3-5% per trade")
    elif regime_name == 'OVERHEAT':
        print(f"  ⚠️ CAUTIOUS LONG — Regime getting hot")
        print(f"  • Reduce position sizes")
        print(f"  • Focus: BTC (safe haven)")
        print(f"  • Risk: 1-2% per trade")
    elif regime_name == 'DEFLATION':
        print(f"  🔻 DEFENSIVE SHORT or FLAT")
        print(f"  • SHORT alts if trend confirms")
        print(f"  • Stables: {alloc.get('STABLES', 0)*100:.0f}%")
        print(f"  • Risk: 1% per trade max")
    elif regime_name == 'STAGFLATION':
        print(f"  🛑 MAXIMUM DEFENSE")
        print(f"  • Minimal trading. Mostly stables.")
        print(f"  • Only SHORT with strong confirmation")
        print(f"  • Risk: 0.5% per trade")
    
    print(f"\n" + "=" * 80)


# ═══════════════════════════════════════════════════════════════
# Section 8: Main & Wrapper
# ═══════════════════════════════════════════════════════════════

class MacroEngine:
    """Wrapper class for external integration (e.g., noogh_wisdom.py)"""
    def __init__(self):
        self.fetcher = MacroDataFetcher()
        self.detector = RegimeDetector()
        self.risk_scorer = RiskAppetiteScorer()
        self.allocator = CryptoAllocator()
        self.corr_monitor = CorrelationMonitor()
        
    def detect_regime(self) -> Dict:
        """Fetch data and determine current overall macro regime."""
        try:
            indicators = self.fetcher.fetch_all()
            regime_name, regime, details = self.detector.detect(indicators)
            risk = self.risk_scorer.score(indicators)
            allocation = self.allocator.allocate(regime, risk, indicators)
            correlation = self.corr_monitor.analyze(indicators)
            
            # Formulate the directive
            if regime_name == 'GOLDILOCKS':
                directive = 'MAXIMUM RISK' if risk['score'] > 0.5 else 'RISK ON'
            elif regime_name == 'OVERHEAT':
                directive = 'NEUTRAL'
            elif regime_name == 'DEFLATION':
                directive = 'DEFENSE'
            else:
                directive = 'MAXIMUM DEFENSE'
                
            return {
                'regime': regime_name,
                'directive': directive,
                'growth_score': details['growth_score'],
                'inflation_score': details['inflation_score'],
                'risk_score': risk['score'],
                'risk_mode': risk['mode'],
                'allocation_weights': allocation['allocation'],
                'max_leverage': allocation['leverage_cap'],
            }
        except Exception as e:
            logger.error(f"MacroEngine error: {e}")
            return {'regime': 'UNKNOWN', 'directive': 'NEUTRAL', 'max_leverage': 5}

def main():
    parser = argparse.ArgumentParser(description='NOOGH Macro Trading Engine')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    args = parser.parse_args()
    
    # 1. Fetch indicators
    logger.info("📡 Fetching macro indicators...")
    fetcher = MacroDataFetcher()
    indicators = fetcher.fetch_all()
    
    # 2. Detect regime
    detector = RegimeDetector()
    regime_name, regime, details = detector.detect(indicators)
    
    # 3. Risk appetite
    risk_scorer = RiskAppetiteScorer()
    risk = risk_scorer.score(indicators)
    
    # 4. Allocation
    allocator = CryptoAllocator()
    allocation = allocator.allocate(regime, risk, indicators)
    
    # 5. Correlation regime
    corr_monitor = CorrelationMonitor()
    correlation = corr_monitor.analyze(indicators)
    
    if args.json:
        print(json.dumps({
            'regime': regime_name,
            'growth_score': details['growth_score'],
            'inflation_score': details['inflation_score'],
            'risk_score': risk['score'],
            'risk_mode': risk['mode'],
            'allocation': allocation,
            'correlation': correlation,
        }, indent=2))
    else:
        generate_report(indicators, regime_name, regime, details, risk, allocation, correlation)


if __name__ == '__main__':
    main()
