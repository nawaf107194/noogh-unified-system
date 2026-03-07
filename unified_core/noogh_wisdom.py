# unified_core/noogh_wisdom.py
"""
NOOGH Sovereign Trading — v3.0 (Brain-Powered Futures)

The Brain (32B Teacher) analyzes real market data and decides:
- LONG or SHORT
- Entry, Take Profit, Stop Loss
- 20x leverage, 30-minute window

Pipeline: Binance Data → Technical Indicators → Brain Analysis → Decision
"""

import logging
import asyncio
import json
import time
import os
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import deque
from dataclasses import dataclass, field

from unified_core.intelligence import CriticalThinker, Evidence

from macro_engine import MacroEngine
from ml_signals import MLPipeline, fetch_klines as ml_fetch_klines
from portfolio_optimizer import HRPOptimizer
from execution_engine import ExecutionSimulator, TWAPAlgorithm, VWAPAlgorithm
from stat_arb import ZScoreEngine, PairConfig, engle_granger_coint

try:
    import aiohttp
except ImportError:
    aiohttp = None

logger = logging.getLogger("unified_core.intelligence.wisdom")

# ═══════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════

LEVERAGE = 10
TRADE_DURATION_MINUTES = 30
# ── Compound Growth Engine: $100 → $1M ──
BASE_RISK_PCT = 0.02       # 2% of balance per trade (base)
WIN_STREAK_BONUS = 0.01    # +1% per 2 wins in streak (up to +2%)
LOSS_RISK_PCT = 0.01       # 1% after loss (anti-martingale)
MAX_RISK_PCT = 0.05        # Never risk more than 5% of balance
MIN_TRADE_USDT = 11         # Min $11 × 10x = $110 notional (Binance min $100)
TARGET_BALANCE = 1_000_000 # 🎯 Target: $1,000,000
MILESTONES = [200, 500, 1_000, 2_500, 5_000, 10_000, 25_000, 50_000, 100_000, 250_000, 500_000, 1_000_000]
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT", "AVAXUSDT"]
DATA_DIR = Path(os.getenv("NOOGH_DATA_DIR",
                Path(__file__).parent.parent / "data")) / "trading"

# ═══════════════════════════════════════════════════════
# Data Structures
# ═══════════════════════════════════════════════════════

@dataclass
class TradeDecision:
    """Brain's trading decision"""
    symbol: str
    direction: str       # LONG or SHORT
    confidence: float    # 0.0-1.0
    entry_price: float
    take_profits: List[float]
    stop_loss: float
    reasoning: str
    leverage: int = LEVERAGE
    duration_min: int = TRADE_DURATION_MINUTES
    timestamp: float = field(default_factory=time.time)
    brain_raw: str = ""
    
    @property
    def risk_reward(self) -> float:
        if not self.take_profits:
            return 0.0
        # Use first TP (TP1) for conservative R:R calculation
        tp1 = self.take_profits[0]
        if self.direction == "LONG":
            risk = abs(self.entry_price - self.stop_loss)
            reward = abs(tp1 - self.entry_price)
        else:
            risk = abs(self.stop_loss - self.entry_price)
            reward = abs(self.entry_price - tp1)
        return reward / risk if risk > 0 else 0
    
    @property
    def icon(self) -> str:
        return "🟢📈" if self.direction == "LONG" else "🔴📉"

@dataclass
class ActiveTrade:
    """Currently active paper trade"""
    decision: TradeDecision
    opened_at: float
    current_price: float = 0.0
    pnl_percent: float = 0.0
    status: str = "OPEN"  # OPEN, TP_HIT, SL_HIT, EXPIRED, CLOSED
    closed_at: float = 0.0
    close_price: float = 0.0

# ═══════════════════════════════════════════════════════
# Technical Analysis (lightweight, pure Python)
# ═══════════════════════════════════════════════════════

class CandlePatterns:
    """كاشف أنماط الشموع اليابانية"""

    @staticmethod
    def body(k: Dict) -> float:
        return abs(k["close"] - k["open"])

    @staticmethod
    def upper_shadow(k: Dict) -> float:
        return k["high"] - max(k["open"], k["close"])

    @staticmethod
    def lower_shadow(k: Dict) -> float:
        return min(k["open"], k["close"]) - k["low"]

    @staticmethod
    def is_bullish(k: Dict) -> bool:
        return k["close"] > k["open"]

    @staticmethod
    def is_bearish(k: Dict) -> bool:
        return k["close"] < k["open"]

    @classmethod
    def detect(cls, klines: List[Dict]) -> List[str]:
        """يكتشف أنماط الشموع ويعيد قائمة بالأنماط المكتشفة"""
        patterns = []
        if len(klines) < 3:
            return patterns

        k1 = klines[-3]
        k2 = klines[-2]
        k  = klines[-1]  # الشمعة الأخيرة

        body_k  = cls.body(k)
        body_k2 = cls.body(k2)
        rng_k   = k["high"] - k["low"] if k["high"] != k["low"] else 0.0001

        # ── Doji ──
        if body_k < rng_k * 0.1:
            patterns.append("Doji (تردد — إشارة انعكاس محتملة)")

        # ── Hammer / Hanging Man ──
        if (cls.lower_shadow(k) > body_k * 2
                and cls.upper_shadow(k) < body_k * 0.5
                and body_k > 0):
            if cls.is_bullish(k):
                patterns.append("Hammer (مطرقة — انعكاس صعودي محتمل)")
            else:
                patterns.append("Hanging Man (رجل مشنوق — انعكاس هبوطي محتمل)")

        # ── Shooting Star / Inverted Hammer ──
        if (cls.upper_shadow(k) > body_k * 2
                and cls.lower_shadow(k) < body_k * 0.5
                and body_k > 0):
            if cls.is_bearish(k):
                patterns.append("Shooting Star (نجمة هاوية — انعكاس هبوطي)")
            else:
                patterns.append("Inverted Hammer (مطرقة مقلوبة — انعكاس صعودي محتمل)")

        # ── Bullish Engulfing ──
        if (cls.is_bearish(k2) and cls.is_bullish(k)
                and k["open"] < k2["close"]
                and k["close"] > k2["open"]):
            patterns.append("Bullish Engulfing (ابتلاع صعودي — إشارة شراء قوية)")

        # ── Bearish Engulfing ──
        if (cls.is_bullish(k2) and cls.is_bearish(k)
                and k["open"] > k2["close"]
                and k["close"] < k2["open"]):
            patterns.append("Bearish Engulfing (ابتلاع هبوطي — إشارة بيع قوية)")

        # ── Morning Star ──
        if (cls.is_bearish(k1)
                and cls.body(k2) < cls.body(k1) * 0.4
                and cls.is_bullish(k)
                and k["close"] > (k1["open"] + k1["close"]) / 2):
            patterns.append("Morning Star (نجمة الصباح — انعكاس صعودي قوي)")

        # ── Evening Star ──
        if (cls.is_bullish(k1)
                and cls.body(k2) < cls.body(k1) * 0.4
                and cls.is_bearish(k)
                and k["close"] < (k1["open"] + k1["close"]) / 2):
            patterns.append("Evening Star (نجمة المساء — انعكاس هبوطي قوي)")

        # ── Three White Soldiers ──
        if (cls.is_bullish(k1) and cls.is_bullish(k2) and cls.is_bullish(k)
                and k2["close"] > k1["close"]
                and k["close"] > k2["close"]):
            patterns.append("Three White Soldiers (ثلاثة جنود بيض — اتجاه صعودي قوي)")

        # ── Three Black Crows ──
        if (cls.is_bearish(k1) and cls.is_bearish(k2) and cls.is_bearish(k)
                and k2["close"] < k1["close"]
                and k["close"] < k2["close"]):
            patterns.append("Three Black Crows (ثلاثة غربان سود — اتجاه هبوطي قوي)")

        # ── Marubozu صعودي ──
        if (cls.is_bullish(k)
                and cls.upper_shadow(k) < body_k * 0.05
                and cls.lower_shadow(k) < body_k * 0.05
                and body_k > rng_k * 0.9):
            patterns.append("Bullish Marubozu (شمعة صعودية كاملة — ضغط شراء قوي)")

        # ── Marubozu هبوطي ──
        if (cls.is_bearish(k)
                and cls.upper_shadow(k) < body_k * 0.05
                and cls.lower_shadow(k) < body_k * 0.05
                and body_k > rng_k * 0.9):
            patterns.append("Bearish Marubozu (شمعة هبوطية كاملة — ضغط بيع قوي)")

        return patterns if patterns else ["لا يوجد نمط واضح"]


class TA:
    """Technical Analysis helpers"""

    @staticmethod
    def sma(data: List[float], p: int) -> float:
        if len(data) < p: return data[-1] if data else 0
        return sum(data[-p:]) / p
    
    @staticmethod
    def ema(data: List[float], p: int) -> float:
        if len(data) < p: return data[-1] if data else 0
        k = 2 / (p + 1)
        val = sum(data[:p]) / p
        for price in data[p:]:
            val = price * k + val * (1 - k)
        return val
    
    @staticmethod
    def rsi(data: List[float], p: int = 14) -> float:
        if len(data) < p + 1: return 50.0
        changes = [data[i] - data[i-1] for i in range(1, len(data))]
        gains = [max(0, c) for c in changes[-p:]]
        losses = [abs(min(0, c)) for c in changes[-p:]]
        ag = sum(gains) / p
        al = sum(losses) / p
        if al == 0: return 100.0
        return 100 - (100 / (1 + ag / al))
    
    @staticmethod
    def bollinger(data: List[float], p: int = 20) -> Tuple[float, float, float]:
        if len(data) < p:
            m = data[-1] if data else 0
            return m, m, m
        w = data[-p:]
        m = sum(w) / p
        std = math.sqrt(sum((x - m)**2 for x in w) / p)
        return m + 2*std, m, m - 2*std
    
    @staticmethod
    def macd(data: List[float]) -> Tuple[float, float, float]:
        if len(data) < 35: return 0, 0, 0
        fast = TA.ema(data, 12)
        slow = TA.ema(data, 26)
        macd_vals = []
        for i in range(10):
            end = len(data) - i
            if end < 26: break
            sub = data[:end]
            macd_vals.insert(0, TA.ema(sub, 12) - TA.ema(sub, 26))
        ml = macd_vals[-1] if macd_vals else 0
        sl = TA.ema(macd_vals, 9) if len(macd_vals) >= 9 else 0
        return ml, sl, ml - sl
    
    @staticmethod
    def atr(highs: List[float], lows: List[float], closes: List[float], p: int = 14) -> float:
        if len(closes) < 2: return 0
        trs = []
        for i in range(1, min(len(highs), len(lows), len(closes))):
            tr = max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))
            trs.append(tr)
        if not trs: return 0
        return sum(trs[-p:]) / min(p, len(trs))
    
    @staticmethod
    def volume_profile(volumes: List[float]) -> str:
        if len(volumes) < 10: return "NORMAL"
        avg = sum(volumes[-20:]) / min(20, len(volumes))
        recent = sum(volumes[-3:]) / 3
        if recent > avg * 2: return "SPIKE"
        if recent > avg * 1.3: return "HIGH"
        if recent < avg * 0.5: return "LOW"
        return "NORMAL"

# ═══════════════════════════════════════════════════════
# Brain Integration (Teacher 32B)
# ═══════════════════════════════════════════════════════

class TradingBrain:
    """Sends market data to Brain (32B Teacher) for analysis"""
    
    def __init__(self):
        self._client = None
    
    async def _get_client(self):
        if self._client is None:
            from .neural_bridge import NeuralEngineClient
            teacher_url = os.getenv("NOOGH_TEACHER_URL", os.getenv("NEURAL_ENGINE_URL"))
            teacher_mode = os.getenv("NOOGH_TEACHER_MODE", os.getenv("NEURAL_ENGINE_MODE", "local"))
            self._client = NeuralEngineClient(base_url=teacher_url, mode=teacher_mode)
            logger.info(f"🧠 Trading Brain: {teacher_mode} → {teacher_url}")
        return self._client
    
    def _build_prompt(self, symbol: str, price: float,
                      indicators: Dict[str, Any],
                      klines_summary: str) -> str:
        """Build analysis prompt — v8 (CScalp Professional Level)"""
        candle_patterns = indicators.get("candle_patterns", ["غير متاح"])
        patterns_str    = "\n".join(f"  • {p}" for p in candle_patterns)
        regime          = indicators.get("market_regime", "UNKNOWN")
        regime_ar = {
            "TRENDING_UP":   "اتجاه صاعد قوي",
            "TRENDING_DOWN":  "اتجاه هابط قوي",
            "RANGING":        "سوق متذبذب",
            "VOLATILE":       "سوق متقلب عالي المخاطر",
            "UNKNOWN":        "غير محدد",
        }.get(regime, regime)

        # MTF
        mtf_note = ""
        if indicators.get("rsi_4h"):
            mtf_note = (
                f"\n=== تأكيد الأطر الزمنية (4h) ===\n"
                f"RSI(4h): {indicators['rsi_4h']:.1f} | "
                f"EMA9(4h): ${indicators.get('ema9_4h', 0):,.2f} | "
                f"Trend(4h): {indicators.get('trend_4h', '?')}"
            )

        # Macro
        dom = indicators.get('dominance', {})
        macro_note = ""
        if dom and dom.get('btc_d'):
            total3_b = dom.get('total3', 0) / 1e9 if dom.get('total3') else 0
            macro_note = (
                f"\n=== السوق الكلي (Macro) ===\n"
                f"BTC.D: {dom.get('btc_d', '?')}% | USDT.D: {dom.get('usdt_d', '?')}% | "
                f"TOTAL3: ${total3_b:.1f}B | "
                f"Signal: {dom.get('signal', 'NEUTRAL')}"
            )

        # Market Structure
        mkt = indicators.get('mkt_structure', {})
        structure_note = ""
        if mkt and mkt.get('structure') not in ('UNKNOWN', None):
            swing_h = ", ".join([f"${v}" for _, v in mkt.get('swing_highs', [])])
            swing_l = ", ".join([f"${v}" for _, v in mkt.get('swing_lows', [])])
            structure_note = (
                f"\n=== هيكل السوق (Market Structure) ===\n"
                f"النمط: {mkt.get('structure', '?')} — {mkt.get('detail', '')}\n"
                f"القمم: {swing_h} | القيعان: {swing_l}\n"
                f"Squeeze: {'نعم ⚡' if mkt.get('is_squeeze') else 'لا'}"
            )

        # S/R Levels
        sr = indicators.get('sr_levels', {})
        sr_note = ""
        sup = sr.get('support', [])
        res = sr.get('resistance', [])
        if sup or res:
            sr_note = (
                f"\n=== مستويات S/R ===\n"
                f"مقاومة: {', '.join([f'${r:,.2f}' for r in res[-4:]] ) or 'لا يوجد'}\n"
                f"دعم: {', '.join([f'${s:,.2f}' for s in sup[-4:]]) or 'لا يوجد'}\n"
                f"⚠️ SL خلف أقرب S/R — ليس نسبة عشوائية"
            )

        # Order Book
        ob = indicators.get('order_book', {})
        ob_note = ""
        if ob and ob.get('bid_volume'):
            walls = ""
            for p, q in ob.get('large_bids', []):
                walls += f"\n  🟢 شراء: ${p:,.2f} ({q:,.0f})"
            for p, q in ob.get('large_asks', []):
                walls += f"\n  🔴 بيع: ${p:,.2f} ({q:,.0f})"
            ob_note = (
                f"\n=== دفتر الأوامر ===\n"
                f"ميزان: {ob.get('imbalance_signal', '?')} ({ob.get('imbalance', 0):+.1f}%) | "
                f"Spread: {ob.get('spread_pct', 0):.4f}%"
                f"{walls}"
            )

        return f"""أنت محلل فيوتشر محترف بأسلوب CScalp. حلل البيانات وقرر صفقة.

=== {symbol} @ ${price:,.2f} ===
الوقت: {datetime.now().strftime('%H:%M:%S')} | نظام: {regime_ar}
{structure_note}
{sr_note}
{ob_note}

=== أنماط الشموع (1h) ===
{patterns_str}

=== المؤشرات (5m) ===
RSI: {indicators.get('rsi', 50):.1f} | EMA9: ${indicators.get('ema_9', 0):,.2f} | EMA21: ${indicators.get('ema_21', 0):,.2f}
BB: Upper=${indicators.get('bb_upper', 0):,.2f} | Lower=${indicators.get('bb_lower', 0):,.2f}
MACD Hist: {indicators.get('macd_hist', 0):.4f} | ATR: ${indicators.get('atr', 0):,.4f} | Vol: {indicators.get('volume_profile', 'NORMAL')}
Change24h: {indicators.get('change_24h', 0):+.2f}%
{mtf_note}
{macro_note}

=== آخر 15 شمعة (1h) ===
{klines_summary}

=== منهجية التحليل ===
1. هيكل السوق:
   • صاعد (HH+HL) → LONG عند ارتداد لقاع أعلى
   • هابط (LH+LL) → SHORT عند ارتداد لقمة أدنى
   • مثلث صاعد → LONG عند اختراق المقاومة المسطحة
   • مثلث هابط → SHORT عند كسر الدعم المسطح
   • ضغط (Squeeze) → ادخل مع اتجاه الاختراق
   • تجميع → خفض الثقة
2. السيولة: الأسعار تنجذب نحو ستوب لوز المتراكمة
3. SL خلف مستوى S/R أو Swing High/Low — ليس نسبة عشوائية
4. TP عند أقرب مقاومة (LONG) أو دعم (SHORT)

=== القرار ===
- LONG أو SHORT (NONE/HOLD ممنوع!)
- SL: خلف S/R — بين 1%-2% من الدخول
- TP: R:R >= 2
- confidence >= 0.75 عند تطابق هيكل + أنماط + Order Book
- confidence 0.55-0.70 عند إشارة جزئية

JSON فقط:
{{"direction": "LONG", "confidence": 0.75, "entry": {price}, "tp": 0, "sl": 0, "reasoning": "تحليل مختصر"}}"""
    
    async def analyze(self, symbol: str, price: float, 
                      indicators: Dict[str, Any],
                      klines_summary: str) -> Optional[TradeDecision]:
        """Send data to Brain and get trade decision"""
        try:
            client = await self._get_client()
            
            prompt = self._build_prompt(symbol, price, indicators, klines_summary)
            
            messages = [
                {"role": "system", "content": "You are NOOGH, an expert futures trader. You MUST respond with ONLY a valid JSON object. No explanations, no reasoning, no text before or after. Just the JSON."},
                {"role": "user", "content": prompt}
            ]
            
            logger.info(f"🧠 Sending {symbol} analysis to Brain...")
        
            result = await client.complete(
                messages=messages,
                max_tokens=2048  # DeepSeek-R1 needs room for reasoning + JSON
            )
            
            if not result or not isinstance(result, dict):
                logger.warning(f"🧠 Brain returned empty response for {symbol}")
                return None
            
            if not result.get("success"):
                logger.warning(f"🧠 Brain call failed for {symbol}: {result.get('error', 'unknown')}")
                return None
            
            response = result.get("content", "")
            if not response:
                logger.warning(f"🧠 Brain returned empty content for {symbol}")
                return None
            
            logger.info(f"🧠 Brain response ({len(response)} chars): {response[:100]}...")
            
            # Parse JSON from response
            decision_data = self._parse_response(response)
            if not decision_data:
                logger.warning(f"🧠 Could not parse Brain response for {symbol}")
                return None
            
            direction = decision_data.get("direction", "").upper()
            if direction not in ("LONG", "SHORT"):
                logger.warning(f"🧠 Invalid direction: {direction}")
                return None
            
            def _clean_float(val: Any, default: float = 0.0) -> float:
                if val is None:
                    return default
                if isinstance(val, str):
                    s = val.replace('$', '').replace(',', '').strip()
                    try:
                        return float(s)
                    except ValueError:
                        return default
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return default
                    
            entry = _clean_float(decision_data.get("entry", price), price)
            tp = _clean_float(decision_data.get("tp", 0), 0.0)
            sl = _clean_float(decision_data.get("sl", 0), 0.0)
            confidence = _clean_float(decision_data.get("confidence", 0.5), 0.5)
            reasoning = decision_data.get("reasoning", "Brain analysis")
            
            # Validate TP/SL make sense
            atr = indicators.get("atr", price * 0.005)
            if atr == 0: atr = price * 0.005

            if direction == "LONG":
                if tp <= entry or sl >= entry:
                    # Fix if brain got confused
                    tp = entry + atr * 2.0
                    sl = entry - atr * 0.7
            else:  # SHORT
                if tp >= entry or sl <= entry:
                    tp = entry - atr * 2.0
                    sl = entry + atr * 0.7

            # v7: Ensure SL is wide enough — min 1.5% from entry (spot)
            # This prevents the SL from being too tight and getting hit in minutes
            MIN_SL_PCT = 0.015  # 1.5% spot = 15% at 10x leverage
            if direction == "LONG":
                sl_pct = abs(entry - sl) / entry
                if sl_pct < MIN_SL_PCT:
                    sl = entry * (1 - MIN_SL_PCT)
                    logger.info(f"🔒 SL widened: {sl_pct:.3%} → {MIN_SL_PCT:.3%} ({symbol})")
            else:  # SHORT
                sl_pct = abs(sl - entry) / entry
                if sl_pct < MIN_SL_PCT:
                    sl = entry * (1 + MIN_SL_PCT)
                    logger.info(f"🔒 SL widened: {sl_pct:.3%} → {MIN_SL_PCT:.3%} ({symbol})")

            # Phase 5: Tiered TPs (TP1, TP2, TP3)
            # TP1: Conservative (+1.5x ATR)
            # TP2: Base Target (+2.0x ATR) 
            # TP3: Runner (+3.0x ATR)
            sl_dist = abs(entry - sl)
            if sl_dist < atr: sl_dist = atr
            
            if direction == "LONG":
                tp1 = entry + (sl_dist * 1.5)
                tp2 = entry + (sl_dist * 2.0)
                tp3 = entry + (sl_dist * 3.0)
            else:
                tp1 = entry - (sl_dist * 1.5)
                tp2 = entry - (sl_dist * 2.0)
                tp3 = entry - (sl_dist * 3.0)

            return TradeDecision(
                symbol=symbol,
                direction=direction,
                confidence=confidence,
                entry_price=entry,
                take_profits=[tp1, tp2, tp3],
                stop_loss=sl,
                reasoning=reasoning,
                brain_raw=response[:500]
            )
            
        except Exception as e:
            logger.error(f"🧠 Brain analysis failed for {symbol}: {e}")
            return None
    
    def _parse_response(self, response: str) -> Optional[Dict]:
        """Extract JSON from Brain response — handles DeepSeek-R1 <think> blocks + raw reasoning"""
        import re
        
        # Step 1: Strip <think>...</think> reasoning blocks (DeepSeek-R1)
        cleaned = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()
        if not cleaned:
            cleaned = response  # fallback if everything was in <think>
        
        # Step 2: Try direct JSON parse
        try:
            return json.loads(cleaned.strip())
        except json.JSONDecodeError:
            pass
        
        # Step 3: Find JSON with balanced braces
        # Scan for all top-level {...} blocks
        candidates = []
        depth = 0
        start = -1
        for i, ch in enumerate(cleaned):
            if ch == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0 and start >= 0:
                    candidates.append(cleaned[start:i+1])
                    start = -1
        
        if candidates:
            logger.debug(f"_parse_response: found {len(candidates)} JSON candidates")
        
        # Try candidates in reverse (JSON usually at end after reasoning)
        for candidate in reversed(candidates):
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict) and ('direction' in parsed or 'Direction' in parsed):
                    return parsed
            except json.JSONDecodeError:
                # Try fixing common issues: trailing commas
                fixed = re.sub(r',\s*}', '}', candidate)
                fixed = re.sub(r',\s*]', ']', fixed)
                try:
                    parsed = json.loads(fixed)
                    if isinstance(parsed, dict) and ('direction' in parsed or 'Direction' in parsed):
                        return parsed
                except json.JSONDecodeError:
                    pass
        
        # Step 4: Try any JSON candidate even without "direction"
        for candidate in reversed(candidates):
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict) and len(parsed) >= 2:
                    return parsed
            except json.JSONDecodeError:
                pass
        
        # Step 5: Try code block ```json ... ```
        code_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', cleaned, re.DOTALL)
        if code_match:
            try:
                return json.loads(code_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Step 6: Last resort — regex for simple flat JSON
        json_match = re.search(r'\{[^{}]*"direction"[^{}]*\}', cleaned, re.DOTALL | re.IGNORECASE)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        logger.warning(f"_parse_response: no JSON found in {len(cleaned)} chars. Last 200: ...{cleaned[-200:]}")
        return None

# ═══════════════════════════════════════════════════════
# Trade Manager (Paper Trading)
# ═══════════════════════════════════════════════════════

class TradeManager:
    """Manages active trades, tracking P&L and exits"""

    # ── Drawdown Protection ──
    MAX_CONSECUTIVE_LOSSES = 4      # إيقاف مؤقت بعد 4 خسائر متتالية
    DRAWDOWN_PAUSE_MINUTES  = 30    # مدة الإيقاف
    MAX_DAILY_LOSS_PCT      = -20.0 # إيقاف عند -20% يومي

    def __init__(self):
        self.active_trades: List[ActiveTrade] = []
        self.trade_history: List[ActiveTrade] = []
        self.stats = {"total": 0, "wins": 0, "losses": 0, "total_pnl": 0.0}
        self._consecutive_losses: int = 0
        self._consecutive_wins: int = 0
        self._pause_until: float = 0.0
        self._daily_pnl: float = 0.0
        self._daily_reset_ts: float = time.time()
        self._last_balance: float = 100.0  # Starting balance
        self._milestone_idx: int = 0
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._load()
        
        # ── Binance Futures Live Execution ──
        self._futures = None
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from trading.binance_futures import BinanceFuturesManager
            self._futures = BinanceFuturesManager(
                testnet=False,
                read_only=False,
                max_leverage=20
            )
            logger.info("🔥 [LIVE] Binance Futures connected — real trading ENABLED")
            # Repair existing positions — set SL/TP if missing
            self._repair_open_positions()
        except Exception as e:
            logger.warning(f"⚠️ Binance Futures unavailable: {e} — paper trading only")
    
    def _repair_open_positions(self):
        """Set SL/TP on any open Binance positions that don't have them"""
        if not self._futures or not self._futures.client:
            return
        try:
            positions = self._futures.get_positions()
            if not positions:
                return
            for pos in positions:
                sym = pos['symbol']
                qty = abs(float(pos.get('positionAmt', 0)))
                entry = float(pos.get('entryPrice', 0))
                if qty <= 0 or entry <= 0:
                    continue
                
                is_long = float(pos.get('positionAmt', 0)) > 0
                order_side = 'SELL' if is_long else 'BUY'
                
                # Check if SL/TP already set
                try:
                    open_orders = self._futures.get_open_orders(sym)
                    has_sl = any(o.get('type') == 'STOP_MARKET' for o in (open_orders or []))
                    has_tp = any(o.get('type') == 'TAKE_PROFIT_MARKET' for o in (open_orders or []))
                    if has_sl and has_tp:
                        logger.info(f"  ✅ {sym}: SL/TP already set")
                        continue
                except Exception:
                    has_sl = has_tp = False
                
                import math
                sl_pct, tp_pct = 0.015, 0.03  # 1.5% SL, 3% TP (R:R = 2:1)
                if is_long:
                    sl = self._futures.round_price(sym, entry * (1 - sl_pct))
                    tp = self._futures.round_price(sym, entry * (1 + tp_pct))
                else:
                    sl = self._futures.round_price(sym, entry * (1 + sl_pct))
                    tp = self._futures.round_price(sym, entry * (1 - tp_pct))
                
                rounded_qty = self._futures.round_quantity(sym, qty)
                logger.info(f"  🔧 Repairing {sym}: SL={sl} TP={tp}")
                
                # Set SL if missing
                if not has_sl:
                    try:
                        self._futures.client.futures_create_order(
                            symbol=sym, side=order_side, type='STOP_MARKET',
                            stopPrice=sl, closePosition=True)
                        logger.info(f"  ✅ {sym} SL set at {sl}")
                    except Exception as e:
                        logger.error(f"  ❌ {sym} SL error: {e}")
                
                # Set TP if missing
                if not has_tp:
                    try:
                        self._futures.client.futures_create_order(
                            symbol=sym, side=order_side, type='TAKE_PROFIT_MARKET',
                            stopPrice=tp, closePosition=True)
                        logger.info(f"  ✅ {sym} TP set at {tp}")
                    except Exception as e:
                        logger.error(f"  ❌ {sym} TP error: {e}")
        except Exception as e:
            logger.error(f"❌ Position repair error: {e}")

    def is_paused(self) -> bool:
        """هل التداول موقوف بسبب Drawdown؟"""
        if time.time() < self._pause_until:
            remaining = (self._pause_until - time.time()) / 60
            logger.warning(f"🛑 [DRAWDOWN] التداول موقوف — متبقي {remaining:.0f} دقيقة")
            return True
        # إعادة ضبط يومي
        if time.time() - self._daily_reset_ts > 86400:
            self._daily_pnl = 0.0
            self._daily_reset_ts = time.time()
        if self._daily_pnl < self.MAX_DAILY_LOSS_PCT:
            logger.warning(f"🛑 [DRAWDOWN] خسارة يومية {self._daily_pnl:.1f}% — توقف حتى الغد")
            return True
        return False

    def _check_drawdown(self, pnl: float):
        """تحديث عداد الخسائر وتفعيل الإيقاف إذا لزم"""
        self._daily_pnl += pnl
        if pnl < 0:
            self._consecutive_losses += 1
            if self._consecutive_losses >= self.MAX_CONSECUTIVE_LOSSES:
                self._pause_until = time.time() + self.DRAWDOWN_PAUSE_MINUTES * 60
                logger.warning(
                    f"🛑 [DRAWDOWN] {self._consecutive_losses} خسائر متتالية "
                    f"— إيقاف {self.DRAWDOWN_PAUSE_MINUTES} دقيقة"
                )
        else:
            self._consecutive_losses = 0
    
    def _get_dynamic_trade_usdt(self, balance: float) -> float:
        """
        🎯 Phase 5: Kelly Criterion Engine (Half-Kelly)
        f* = W - ((1 - W) / R)
        W = Win Rate, R = Avg Win / Avg Loss
        """
        # Default fallback sizing (if no data)
        base_trade_pct = 0.02
        default_trade = max(balance * base_trade_pct, MIN_TRADE_USDT)
        
        # During deep drawdown, apply anti-martingale penalty
        if self._consecutive_losses >= 2:
            logger.info(f"  🔻 [RISK] Drawdown mode: 1% risk size.")
            return max(balance * LOSS_RISK_PCT, MIN_TRADE_USDT)

        # Analyze rolling window of last 50 trades
        recent_trades = self.trade_history[-50:]
        if len(recent_trades) < 5:  # Not enough data for Kelly Kelly
            return default_trade

        wins = [t.pnl_percent for t in recent_trades if t.pnl_percent > 0]
        losses = [abs(t.pnl_percent) for t in recent_trades if t.pnl_percent < 0]

        win_rate = len(wins) / len(recent_trades)
        
        if len(losses) == 0:
            avg_loss = 1.0  # Prevent div zero
        else:
            avg_loss = sum(losses) / len(losses)
            
        avg_win = sum(wins) / len(wins) if len(wins) > 0 else 0.0
        
        # Risk-Reward Ratio (R)
        R = avg_win / avg_loss if avg_loss > 0 else 0
        
        # Kelly Fraction (f*)
        if R <= 0:
            kelly_f = 0
        else:
            # f* = W - ((1 - W) / R)
            kelly_f = win_rate - ((1 - win_rate) / R)
            
        # Apply Half-Kelly (dampen volatility and handle variance)
        half_kelly = kelly_f / 2.0
        
        # Enforce bounds: minimum 1%, maximum 10% per trade
        risk_pct = max(min(half_kelly, 0.10), 0.01)
        
        trade_usdt = balance * risk_pct
        trade_usdt = max(trade_usdt, MIN_TRADE_USDT)
        
        logger.info(
            f"  🧠 [KELLY] W: {win_rate:.0%} | R: {R:.2f} | f*: {kelly_f:.2%} -> Risking {risk_pct:.1f}% (${trade_usdt:.2f})"
        )
        
        return trade_usdt
    
    def _check_milestones(self, balance: float):
        """🏆 Track progress toward $1M target"""
        while self._milestone_idx < len(MILESTONES) and balance >= MILESTONES[self._milestone_idx]:
            milestone = MILESTONES[self._milestone_idx]
            growth = (balance / 100) * 100  # % from starting $100
            logger.info(f"")
            logger.info(f"╔{'═'*58}╗")
            logger.info(f"║  🏆 MILESTONE REACHED: ${milestone:,.0f}               ║")
            logger.info(f"║  📈 Growth: {growth:,.0f}% from $100                    ║")
            logger.info(f"║  💰 Current Balance: ${balance:,.2f}                  ║")
            remaining = TARGET_BALANCE - balance
            logger.info(f"║  🎯 Remaining to $1M: ${remaining:,.0f}              ║")
            logger.info(f"╚{'═'*58}╝")
            self._milestone_idx += 1
        
        self._last_balance = balance
    
    def open_trade(self, decision: TradeDecision):
        """Open a trade — paper + live Binance Futures execution"""
        trade = ActiveTrade(
            decision=decision,
            opened_at=time.time(),
            current_price=decision.entry_price
        )
        self.active_trades.append(trade)
        self.stats["total"] += 1
        
        logger.info(
            f"{'🟢' if decision.direction == 'LONG' else '🔴'} "
            f"فتح صفقة {decision.direction} {decision.symbol} "
            f"@ ${decision.entry_price:,.2f} | "
            f"TPs: {[f'${tp:,.2f}' for tp in decision.take_profits]} | SL: ${decision.stop_loss:,.2f} | "
            f"R:R={decision.risk_reward:.1f} | "
            f"رافعة: {decision.leverage}x | "
            f"ثقة: {decision.confidence:.0%}"
        )
        
        # ── 🎯 Dynamic position sizing: compound growth ──
        # In a real live environment, we check actual USDT free.
        # For simulation/paper, assume $1000 base
        usdt_free = 1000.0
        if self._futures:
            try:
                bal = self._futures.get_futures_balance()
                if bal:
                    for b in bal:
                        if b.get('asset') == 'USDT':
                            usdt_free = float(b.get('availableBalance', b.get('balance', 0)))
                            break
            except Exception:
                pass
                
        trade_usdt = self._get_dynamic_trade_usdt(usdt_free)
        quantity = (trade_usdt * decision.leverage) / decision.entry_price
        side = "BUY" if decision.direction == "LONG" else "SELL"
        
        # ═══════ Phase 4: Execution Engine (VWAP) ═══════
        logger.info(f"  🤖 [EXECUTION] Routing {side} {quantity:.4f} {decision.symbol} to VWAP Algo...")
        # Simulate execution slippage and impact
        # We assume 5 minutes execution using VWAP
        try:
            import sys
            import numpy as np
            from execution_engine import VWAPAlgorithm
            dummy_vols = np.array([1000] * 30) # 30 slices for 5 minutes
            
            vwap_algo = VWAPAlgorithm()
            slices = vwap_algo.generate_schedule(quantity, dummy_vols, 300, decision.entry_price)
            
            if slices:
                # Add simulated slippage to the slices
                total_qty = 0
                total_value = 0
                for i, s in enumerate(slices):
                    # add small random slippage curve
                    slip_factor = 1 + (i - 15) * 0.0001
                    fill_price = s.expected_price * slip_factor
                    total_value += fill_price * s.quantity
                    total_qty += s.quantity
                
                exec_price = total_value / total_qty
                slippage = abs(exec_price - decision.entry_price) / decision.entry_price * 100
                decision.entry_price = exec_price
                trade.current_price = exec_price
                logger.info(f"   ✅ [EXECUTION] Filled @ ${exec_price:,.4f} ({len(slices)} slices) | Slippage: {slippage:.3f}%")
            else:
                logger.warning("   ⚠️ [EXECUTION] VWAP failed to generate slices, using requested price")
                exec_price = decision.entry_price
        except Exception as e:
            logger.warning(f"   ⚠️ [EXECUTION] VWAP error: {e}, using requested price")
            exec_price = decision.entry_price
        
        # ── Live Binance Futures Execution ──
        if self._futures:
            try:
                # Balance check: require min $5 USDT
                if usdt_free < 5.0:
                    logger.warning(f"🛑 [الرصيد] USDT غير كافي: ${usdt_free:.2f} < $5.00 — لا تنفيذ حقيقي")
                    self._save()
                    return trade
                
                logger.info(f"  💰 [{decision.symbol}] الرصيد المتاح: ${usdt_free:.2f}")
                
                result = self._futures.open_position(
                    symbol=decision.symbol,
                    side=side,
                    quantity=quantity,
                    leverage=decision.leverage,
                    stop_loss=decision.stop_loss,
                    # We will handle TP manually via multiple tiered orders
                    take_profit=None 
                )
                
                if "error" in result:
                    logger.error(f"❌ [LIVE] Binance order FAILED: {result['error']}")
                else:
                    order_id = result.get('order_id', '?')
                    exec_qty = result.get('executed_qty', quantity)
                    has_sl = '✅' if result.get('stop_loss') else '❌'
                    
                    logger.info(
                        f"✅ [LIVE] Binance order #{order_id} EXECUTED: "
                        f"{side} {exec_qty} {decision.symbol} | SL: {has_sl}"
                    )
                    
                    # Phase 5: Execute Tiered Take Profits
                    if decision.take_profits and len(decision.take_profits) == 3:
                        order_side = "SELL" if side == "BUY" else "BUY"
                        
                        tp1, tp2, tp3 = decision.take_profits
                        qty1 = self._futures.round_quantity(decision.symbol, float(exec_qty) * 0.50)
                        qty2 = self._futures.round_quantity(decision.symbol, float(exec_qty) * 0.30)
                        qty3 = self._futures.round_quantity(decision.symbol, float(exec_qty) * 0.20)
                        
                        try:
                            # TP1 (50%)
                            if qty1 > 0:
                                self._futures.client.futures_create_order(
                                    symbol=decision.symbol, side=order_side, type="TAKE_PROFIT_MARKET",
                                    stopPrice=self._futures.round_price(decision.symbol, tp1),
                                    quantity=qty1
                                )
                            # TP2 (30%)
                            if qty2 > 0:
                                self._futures.client.futures_create_order(
                                    symbol=decision.symbol, side=order_side, type="TAKE_PROFIT_MARKET",
                                    stopPrice=self._futures.round_price(decision.symbol, tp2),
                                    quantity=qty2
                                )
                            # TP3 (20%)
                            if qty3 > 0:
                                self._futures.client.futures_create_order(
                                    symbol=decision.symbol, side=order_side, type="TAKE_PROFIT_MARKET",
                                    stopPrice=self._futures.round_price(decision.symbol, tp3),
                                    quantity=qty3
                                )
                            logger.info(f"   🎯 [TIERED-TP] 3 scaled orders submitted successfully")
                        except Exception as e:
                            logger.error(f"   ❌ [TIERED-TP] Error executing scale-out: {e}")
                            
            except Exception as e:
                logger.error(f"❌ [LIVE] Binance execution error: {e}")
        
        self._save()
        return trade
    
    def open_pair_trade(self, pair: str, direction: str, z_score: float):
        """Phase 4: Specialized method for executing Stat-Arb pair trades (e.g. ETH/SOL)"""
        sym1, sym2 = pair.split('/')
        logger.info(f"  ⚖️ [STAT-ARB] Executing {direction} on {pair} @ Z-Score: {z_score:+.2f}")
        
        usdt_free = 1000.0
        if self._futures:
            try:
                bal = self._futures.get_futures_balance()
                if bal:
                    for b in bal:
                        if b.get('asset') == 'USDT':
                            usdt_free = float(b.get('availableBalance', b.get('balance', 0)))
                            break
            except Exception:
                pass
                
        if usdt_free < 20.0:
            logger.warning(f"🛑 [STAT-ARB] Insufficient USDT for pair trade: ${usdt_free:.2f}")
            return
            
        trade_usdt = self._get_dynamic_trade_usdt(usdt_free) / 2.0  # Split capital
        
        # Determine legs
        if direction == "LONG_SPREAD":
            leg1_side, leg2_side = "BUY", "SELL"
        else:
            leg1_side, leg2_side = "SELL", "BUY"
            
        # We would normally use VWAP execution for both legs here
        logger.info(f"   ✅ [STAT-ARB] Leg 1: {leg1_side} {sym1} for ${trade_usdt:.2f} (Paper)")
        logger.info(f"   ✅ [STAT-ARB] Leg 2: {leg2_side} {sym2} for ${trade_usdt:.2f} (Paper)")
        
    def update_prices(self, prices: Dict[str, float]):
        """Update active trades with current prices + Trailing SL"""
        for trade in self.active_trades[:]:
            if trade.status != "OPEN":
                continue

            symbol = trade.decision.symbol
            if symbol not in prices:
                continue

            price = prices[symbol]
            trade.current_price = price
            d = trade.decision

            # Calculate P&L
            if d.direction == "LONG":
                trade.pnl_percent = ((price - d.entry_price) / d.entry_price) * 100 * d.leverage
            else:
                trade.pnl_percent = ((d.entry_price - price) / d.entry_price) * 100 * d.leverage

            # ── Trailing Stop Loss ──
            # يتحرك SL لتأمين الأرباح عند الربح >= 5% (leveraged)
            TRAIL_TRIGGER_PCT = 5.0   # تفعيل عند +5%
            TRAIL_OFFSET_PCT  = 0.002 # 0.2% خلف السعر الحالي
            if trade.pnl_percent >= TRAIL_TRIGGER_PCT:
                if d.direction == "LONG":
                    new_sl = price * (1 - TRAIL_OFFSET_PCT)
                    if new_sl > d.stop_loss:
                        d.stop_loss = new_sl
                        logger.debug(f"📈 [TRAIL] {symbol} SL moved to ${new_sl:,.4f}")
                else:  # SHORT
                    new_sl = price * (1 + TRAIL_OFFSET_PCT)
                    if new_sl < d.stop_loss:
                        d.stop_loss = new_sl
                        logger.debug(f"📉 [TRAIL] {symbol} SL moved to ${new_sl:,.4f}")

            # ── Check Tiered TPs ──
            if d.take_profits:
                tp_target = d.take_profits[0]
                tp_hit = False
                if d.direction == "LONG" and price >= tp_target:
                    tp_hit = True
                elif d.direction == "SHORT" and price <= tp_target:
                    tp_hit = True
                    
                if tp_hit:
                    # Pop the achieved TP level
                    hit_level = len(d.take_profits)
                    d.take_profits.pop(0)
                    
                    if hit_level == 3:
                        logger.info(f"   🎯 [TP1 HIT] {symbol} secured 50% at ${tp_target:,.4f}. SL moved to entry.")
                        d.stop_loss = d.entry_price  # Move SL to entry on TP1
                    elif hit_level == 2:
                        logger.info(f"   🎯 [TP2 HIT] {symbol} secured 30% at ${tp_target:,.4f}.")
                    
                    # If all TPs hit, or this was the last one, close out fully
                    if not d.take_profits:
                        logger.info(f"   🚀 [TP3 HIT] {symbol} fully exited at ${tp_target:,.4f}!")
                        self._close_trade(trade, "TP_HIT", tp_target)
                        continue

            # Check SL
            if d.direction == "LONG" and price <= d.stop_loss:
                self._close_trade(trade, "SL_HIT", d.stop_loss)
            elif d.direction == "SHORT" and price >= d.stop_loss:
                self._close_trade(trade, "SL_HIT", d.stop_loss)

            # Check expiry (30 min)
            elif time.time() - trade.opened_at > d.duration_min * 60:
                self._close_trade(trade, "EXPIRED", price)
    
    def _close_trade(self, trade: ActiveTrade, reason: str, price: float):
        """Close a trade — paper + real Binance position"""
        trade.status = reason
        trade.close_price = price
        trade.closed_at = time.time()
        d = trade.decision
        
        if d.direction == "LONG":
            trade.pnl_percent = ((price - d.entry_price) / d.entry_price) * 100 * d.leverage
        else:
            trade.pnl_percent = ((d.entry_price - price) / d.entry_price) * 100 * d.leverage
        
        result_icon = "✅" if trade.pnl_percent > 0 else "❌"
        duration = (trade.closed_at - trade.opened_at) / 60
        
        if trade.pnl_percent > 0:
            self.stats["wins"] += 1
            self._consecutive_wins += 1
            self._consecutive_losses = 0
            # 🏆 Reward: log the win and streak
            if self._consecutive_wins >= 3:
                logger.info(f"  🔥 WIN STREAK x{self._consecutive_wins}! الحجم القادم أكبر!")
        else:
            self.stats["losses"] += 1
            self._consecutive_wins = 0
        self.stats["total_pnl"] += trade.pnl_percent
        self._check_drawdown(trade.pnl_percent)
        
        # 🏆 Check milestones → $1M target
        if self._futures:
            try:
                bal = self._futures.get_futures_balance()
                if bal:
                    for b in bal:
                        if b.get('asset') == 'USDT':
                            current_bal = float(b.get('balance', 0))
                            self._check_milestones(current_bal)
                            break
            except Exception:
                pass
        
        logger.info(
            f"{result_icon} إغلاق {d.direction} {d.symbol} | "
            f"السبب: {reason} | "
            f"P&L: {trade.pnl_percent:+.2f}% ({trade.pnl_percent/d.leverage:+.2f}% spot) | "
            f"المدة: {duration:.1f} دقيقة | "
            f"الدخول: ${d.entry_price:,.2f} → الخروج: ${price:,.2f}"
        )
        
        # ── Close real Binance position on EXPIRY ──
        # SL/TP hit = Binance already closed via STOP_MARKET/TAKE_PROFIT_MARKET
        # EXPIRED = must close manually
        if self._futures and reason == "EXPIRED":
            try:
                # Cancel pending SL/TP orders for this symbol
                self._futures.cancel_all_orders(d.symbol)
                logger.info(f"  🗑️ [{d.symbol}] Cancelled pending SL/TP orders")
                
                # Close the position
                close_result = self._futures.close_position(d.symbol)
                if close_result and 'error' not in close_result:
                    logger.info(f"  ✅ [{d.symbol}] Binance position CLOSED")
                else:
                    logger.warning(f"  ⚠️ [{d.symbol}] Binance close: {close_result}")
            except Exception as e:
                logger.error(f"  ❌ [{d.symbol}] Binance close error: {e}")
        elif self._futures and reason in ("SL_HIT", "TP_HIT"):
            # Binance auto-closed via STOP_MARKET/TAKE_PROFIT_MARKET
            # Just cancel remaining pending orders
            try:
                self._futures.cancel_all_orders(d.symbol)
                logger.info(f"  🗑️ [{d.symbol}] Cleaned up remaining orders")
            except Exception:
                pass
        
        self.active_trades.remove(trade)
        self.trade_history.append(trade)
        self._save()
    
    def get_active_count(self, symbol: str = None) -> int:
        """Count active trades, optionally for a specific symbol"""
        if symbol:
            return sum(1 for t in self.active_trades 
                      if t.status == "OPEN" and t.decision.symbol == symbol)
        return sum(1 for t in self.active_trades if t.status == "OPEN")
    
    def _save(self):
        """Save trade history to disk"""
        try:
            history_data = []
            for t in self.trade_history[-100:]:
                d = t.decision
                history_data.append({
                    "symbol": d.symbol, "direction": d.direction,
                    "entry": d.entry_price, "tp": d.take_profits, "sl": d.stop_loss,
                    "confidence": d.confidence, "reasoning": d.reasoning,
                    "opened_at": t.opened_at, "closed_at": t.closed_at,
                    "close_price": t.close_price, "pnl_percent": t.pnl_percent,
                    "status": t.status, "leverage": d.leverage
                })
            
            save_data = {"stats": self.stats, "history": history_data}
            path = DATA_DIR / "trade_history.json"
            with open(path, "w") as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.debug(f"Trade save error: {e}")
    
    def _load(self):
        """Load trade history from disk"""
        try:
            path = DATA_DIR / "trade_history.json"
            if path.exists():
                with open(path) as f:
                    data = json.load(f)
                self.stats = data.get("stats", self.stats)
                logger.info(
                    f"📊 Loaded trade history: "
                    f"{self.stats['total']} trades, "
                    f"{self.stats['wins']}W/{self.stats['losses']}L, "
                    f"P&L: {self.stats['total_pnl']:+.2f}%"
                )
        except Exception as e:
            logger.debug(f"Trade load error: {e}")

# ═══════════════════════════════════════════════════════
# Market Data Fetcher
# ═══════════════════════════════════════════════════════

class MarketDataFetcher:
    """Fetches real market data from Binance"""
    
    BASE = "https://api.binance.com/api/v3"
    
    async def fetch_ticker(self, symbols: List[str]) -> Dict[str, float]:
        """Fetch current prices"""
        prices = {}
        if not aiohttp: return prices
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as s:
                async with s.get(f"{self.BASE}/ticker/price") as r:
                    if r.status == 200:
                        for item in await r.json():
                            if item["symbol"] in symbols:
                                prices[item["symbol"]] = float(item["price"])
        except Exception as e:
            logger.error(f"❌ Price fetch error: {e}")
        return prices
    
    async def fetch_24h(self, symbol: str) -> Dict[str, float]:
        """Fetch 24h stats"""
        if not aiohttp: return {}
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as s:
                async with s.get(f"{self.BASE}/ticker/24hr", params={"symbol": symbol}) as r:
                    if r.status == 200:
                        d = await r.json()
                        return {
                            "change_24h": float(d.get("priceChangePercent", 0)),
                            "volume_24h": float(d.get("quoteVolume", 0)),
                            "high_24h": float(d.get("highPrice", 0)),
                            "low_24h": float(d.get("lowPrice", 0)),
                        }
        except Exception:
            pass
        return {}
    
    async def fetch_klines(self, symbol: str, interval: str = "1h", 
                           limit: int = 15) -> List[Dict]:
        """Fetch kline/candlestick data"""
        if not aiohttp: return []
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as s:
                params = {"symbol": symbol, "interval": interval, "limit": limit}
                async with s.get(f"{self.BASE}/klines", params=params) as r:
                    if r.status == 200:
                        raw = await r.json()
                        return [
                            {
                                "time": datetime.fromtimestamp(k[0]/1000).strftime("%H:%M"),
                                "open": float(k[1]), "high": float(k[2]),
                                "low": float(k[3]), "close": float(k[4]),
                                "volume": float(k[5])
                            }
                            for k in raw
                        ]
        except Exception:
            pass
        return []
    
    def format_klines(self, klines: List[Dict]) -> str:
        """Format klines as readable text for Brain"""
        if not klines:
            return "لا توجد بيانات"
        lines = ["الوقت    | الفتح      | الأعلى     | الأدنى     | الإغلاق    | الحجم"]
        lines.append("-" * 75)
        for k in klines[-15:]:
            lines.append(
                f"{k['time']:8} | "
                f"${k['open']:>10,.2f} | "
                f"${k['high']:>10,.2f} | "
                f"${k['low']:>10,.2f} | "
                f"${k['close']:>10,.2f} | "
                f"{k['volume']:>10,.0f}"
            )
        return "\n".join(lines)
    
    async def fetch_order_book(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        """Fetch order book depth — find large orders and bid/ask imbalance"""
        if not aiohttp: return {}
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as s:
                params = {"symbol": symbol, "limit": limit}
                async with s.get(f"{self.BASE}/depth", params=params) as r:
                    if r.status == 200:
                        data = await r.json()
                        bids = [(float(p), float(q)) for p, q in data.get("bids", [])]
                        asks = [(float(p), float(q)) for p, q in data.get("asks", [])]
                        
                        total_bid_vol = sum(q for _, q in bids)
                        total_ask_vol = sum(q for _, q in asks)
                        
                        # Find large orders (walls)
                        avg_qty = (total_bid_vol + total_ask_vol) / (len(bids) + len(asks)) if bids and asks else 0
                        large_bids = [(p, q) for p, q in bids if q > avg_qty * 3]
                        large_asks = [(p, q) for p, q in asks if q > avg_qty * 3]
                        
                        # Bid/Ask imbalance
                        imbalance = (total_bid_vol - total_ask_vol) / (total_bid_vol + total_ask_vol) * 100 if (total_bid_vol + total_ask_vol) > 0 else 0
                        
                        return {
                            "bid_volume": total_bid_vol,
                            "ask_volume": total_ask_vol,
                            "imbalance": round(imbalance, 1),  # +ve = buyers, -ve = sellers
                            "imbalance_signal": "BUYERS" if imbalance > 15 else "SELLERS" if imbalance < -15 else "BALANCED",
                            "large_bids": large_bids[:3],  # top 3 whale buy walls
                            "large_asks": large_asks[:3],  # top 3 whale sell walls
                            "best_bid": bids[0][0] if bids else 0,
                            "best_ask": asks[0][0] if asks else 0,
                            "spread_pct": round((asks[0][0] - bids[0][0]) / bids[0][0] * 100, 4) if bids and asks else 0
                        }
        except Exception:
            pass
        return {}
    
    @staticmethod
    def detect_support_resistance(klines: List[Dict], window: int = 3) -> Dict[str, List[float]]:
        """Detect key support/resistance levels from klines using pivot points"""
        if len(klines) < window * 2 + 1:
            return {"support": [], "resistance": []}
        
        highs = [k["high"] for k in klines]
        lows = [k["low"] for k in klines]
        
        resistance_levels = []
        support_levels = []
        
        for i in range(window, len(klines) - window):
            # Pivot high = local maximum
            if all(highs[i] >= highs[i-j] for j in range(1, window+1)) and \
               all(highs[i] >= highs[i+j] for j in range(1, window+1)):
                resistance_levels.append(highs[i])
            
            # Pivot low = local minimum
            if all(lows[i] <= lows[i-j] for j in range(1, window+1)) and \
               all(lows[i] <= lows[i+j] for j in range(1, window+1)):
                support_levels.append(lows[i])
        
        # Cluster nearby levels (within 0.3%)
        def cluster(levels, threshold=0.003):
            if not levels:
                return []
            levels = sorted(levels)
            result = [levels[0]]
            for lvl in levels[1:]:
                if abs(lvl - result[-1]) / result[-1] > threshold:
                    result.append(lvl)
                else:
                    result[-1] = (result[-1] + lvl) / 2  # average nearby levels
            return result
        
        return {
            "support": cluster(support_levels),
            "resistance": cluster(resistance_levels)
        }
    
    @staticmethod
    def detect_market_structure(klines: List[Dict]) -> Dict[str, Any]:
        """
        Detect market structure: HH/HL (bullish), LH/LL (bearish), or consolidation.
        Also detects: squeeze, channel, triangle patterns.
        """
        if len(klines) < 10:
            return {"structure": "UNKNOWN", "detail": "بيانات غير كافية"}
        
        highs = [k["high"] for k in klines]
        lows = [k["low"] for k in klines]
        closes = [k["close"] for k in klines]
        
        # Find swing highs and lows (window=2)
        swing_highs = []
        swing_lows = []
        for i in range(2, len(klines) - 2):
            if highs[i] >= highs[i-1] and highs[i] >= highs[i-2] and \
               highs[i] >= highs[i+1] and highs[i] >= highs[i+2]:
                swing_highs.append((i, highs[i]))
            if lows[i] <= lows[i-1] and lows[i] <= lows[i-2] and \
               lows[i] <= lows[i+1] and lows[i] <= lows[i+2]:
                swing_lows.append((i, lows[i]))
        
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return {"structure": "UNCLEAR", "detail": "لا يوجد هيكل واضح"}
        
        # Check for higher highs / higher lows (bullish structure)
        hh = swing_highs[-1][1] > swing_highs[-2][1]  # Higher High
        hl = swing_lows[-1][1] > swing_lows[-2][1]     # Higher Low
        lh = swing_highs[-1][1] < swing_highs[-2][1]   # Lower High  
        ll = swing_lows[-1][1] < swing_lows[-2][1]      # Lower Low
        
        # Detect squeeze (range getting tighter)
        recent_range = max(highs[-5:]) - min(lows[-5:])
        older_range = max(highs[-15:-5]) - min(lows[-15:-5]) if len(klines) >= 15 else recent_range
        is_squeeze = recent_range < older_range * 0.5
        
        # Detect ascending/descending triangle
        highs_flat = abs(swing_highs[-1][1] - swing_highs[-2][1]) / swing_highs[-1][1] < 0.002
        lows_rising = swing_lows[-1][1] > swing_lows[-2][1]
        lows_flat = abs(swing_lows[-1][1] - swing_lows[-2][1]) / swing_lows[-1][1] < 0.002
        highs_falling = swing_highs[-1][1] < swing_highs[-2][1]
        
        if highs_flat and lows_rising:
            pattern = "ASCENDING_TRIANGLE"
            detail = "مثلث صاعد — قمم مستوية + قيعان صاعدة → اختراق صاعد متوقع"
        elif lows_flat and highs_falling:
            pattern = "DESCENDING_TRIANGLE"
            detail = "مثلث هابط — قيعان مستوية + قمم هابطة → اختراق هابط متوقع"
        elif is_squeeze:
            pattern = "SQUEEZE"
            detail = "ضغط سعري (Squeeze) — النطاق يضيق → حركة قوية قادمة"
        elif hh and hl:
            pattern = "BULLISH_STRUCTURE"
            detail = "هيكل صاعد — قمم أعلى + قيعان أعلى (Higher Highs + Higher Lows)"
        elif lh and ll:
            pattern = "BEARISH_STRUCTURE"
            detail = "هيكل هابط — قمم أدنى + قيعان أدنى (Lower Highs + Lower Lows)"
        elif hh and ll:
            pattern = "EXPANSION"
            detail = "توسع — النطاق يتوسع (تقلب متزايد)"
        else:
            pattern = "CONSOLIDATION"
            detail = "تجميع/توزيع — السعر يتذبذب بدون اتجاه واضح"
        
        return {
            "structure": pattern,
            "detail": detail,
            "swing_highs": [(i, round(v, 4)) for i, v in swing_highs[-3:]],
            "swing_lows": [(i, round(v, 4)) for i, v in swing_lows[-3:]],
            "is_squeeze": is_squeeze,
            "hh": hh, "hl": hl, "lh": lh, "ll": ll
        }

# ═══════════════════════════════════════════════════════
# Main Engine (Public API)
# ═══════════════════════════════════════════════════════

class NooghWisdomEngine:
    """محرك الحكمة — v3.0"""
    BINANCE_TICKER_URL = "https://api.binance.com/api/v3/ticker/price"
    
    def __init__(self):
        self.symbols = SYMBOLS
        self.last_prices = {}
    
    async def fetch_market_prices(self) -> Dict[str, float]:
        """Backward compat — used by system_monitor"""
        if not aiohttp: return {}
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as s:
                async with s.get(self.BINANCE_TICKER_URL) as r:
                    if r.status == 200:
                        for item in await r.json():
                            if item['symbol'] in self.symbols:
                                self.last_prices[item['symbol']] = float(item['price'])
        except Exception:
            pass
        return self.last_prices


class AdvancedNooghWisdom:
    """المحرك الرئيسي للتداول السيادي مع الحكمة (Phase 4: Multi-Strategy)"""
    
    POLL_INTERVAL = 30
    MIN_TRADES = 50
    # GS Quant Filters
    MAX_CONCURRENT_POSITIONS = 3
    MAX_DAILY_TRADES = 20
    LOSS_COOLDOWN_SEC = 300
    NO_TRADE_ZONE = 0.20
    def __init__(self, futures_client=None):
        self.MAX_DAILY_LOSS_PCT = 15.0  # عتبة التوقف اليومي
        self.fetcher = MarketDataFetcher()
        self.trade_mgr = TradeManager()
        self.brain = TradingBrain()  # Initializes NeuralEngineClient connection
        self._cycle_count = 0
        
        # ── Institutional Quant Engines (Phase 4) ──
        self.macro_engine = MacroEngine()
        self.hrp_optimizer = HRPOptimizer()
        self.ml_pipeline = MLPipeline(n_estimators=80, lr=0.1, n_folds=4, horizon=5)
        
        self._last_ml_train_time = 0
        self._ml_signals = {}  # {symbol: float}
        self._portfolio_weights = {}  # {symbol: float}
        self._current_regime = "UNKNOWN"
        self._regime_directive = "NEUTRAL"
        self.price_history = {}  # {symbol: [prices...]}
        
        # ── GS Phase 1: State tracking ──
        self._last_loss_time = 0        # Timestamp of last losing trade
        self._daily_trade_count = 0     # Trades opened today
        self._daily_reset_date = ""     # Reset counter daily

        # ── أنظمة مُولَّدة ذاتياً (تكامل v6) ──
        try:
            from unified_core.intelligence.funding_rate_filter import FundingRateFilter
            self._funding_filter = FundingRateFilter()
            logger.info("✅ [v6] FundingRateFilter مُفعَّل")
        except Exception:
            self._funding_filter = None

        try:
            from unified_core.intelligence.btc_correlation_guard import BtcCorrelationGuard
            self._btc_guard = BtcCorrelationGuard()
            logger.info("✅ [v6] BtcCorrelationGuard مُفعَّل")
        except Exception:
            self._btc_guard = None

        try:
            from unified_core.intelligence.pattern_scoring import PatternScorer
            self._pattern_scorer = PatternScorer()
            logger.info("✅ [v6] PatternScorer مُفعَّل")
        except Exception:
            self._pattern_scorer = None
    
    def compute_composite_score(self, indicators: Dict[str, Any], 
                                ml_signal: float = 0.0, 
                                macro_bias: str = "NEUTRAL") -> Dict[str, Any]:
        """
        Phase 4 Composite Score:
        Blends GS Quant rules (50%), ML prediction (40%), and Macro Bias (10%).
        Returns score -1.0 (strong bearish) to +1.0 (strong bullish).
        """
        # ── 1. GS Base Score (weight: 0.50) ──
        # A. Momentum Score (weight: 0.30 of GS)
        rsi = indicators.get('rsi', 50)
        rsi_norm = (rsi - 50) / 50  # -1 to +1
        
        macd_hist = indicators.get('macd_hist', 0)
        atr = indicators.get('atr', 1)
        macd_norm = max(min(macd_hist / atr if atr else 0, 1), -1)
        
        ema9 = indicators.get('ema_9', 0)
        ema21 = indicators.get('ema_21', 0)
        ema_cross = 1.0 if ema9 > ema21 else -1.0
        
        s_momentum = 0.4 * rsi_norm + 0.4 * macd_norm + 0.2 * ema_cross
        
        # B. Structure Score (weight: 0.25 of GS)
        mkt = indicators.get('mkt_structure', {})
        struct = mkt.get('structure', '') if mkt else ''
        sma50 = indicators.get('sma_50', 0)
        price = indicators.get('ema_9', 0)  # approximate current price
        
        struct_map = {
            'BULLISH_STRUCTURE': 0.8,
            'ASCENDING_TRIANGLE': 1.0,
            'BEARISH_STRUCTURE': -0.8,
            'DESCENDING_TRIANGLE': -1.0,
            'EXPANSION': 0.0,
            'CONSOLIDATION': 0.0,
            'UNCLEAR': 0.0,
            'UNKNOWN': 0.0,
        }
        s_structure = struct_map.get(struct, 0.0)
        if struct == 'SQUEEZE' and sma50:
            s_structure = 0.6 if price > sma50 else -0.6
        
        # C. Order Flow Score (weight: 0.20 of GS)
        ob = indicators.get('order_book', {})
        imbalance = ob.get('imbalance', 0) if ob else 0
        imbalance_norm = max(min(imbalance / 30, 1), -1)
        
        large_bids = ob.get('large_bids', []) if ob else []
        large_asks = ob.get('large_asks', []) if ob else []
        wall_score = 0.0
        if large_bids and not large_asks:
            wall_score = 0.5
        elif large_asks and not large_bids:
            wall_score = -0.5
        
        s_orderflow = 0.6 * imbalance_norm + 0.4 * wall_score
        
        # D. Multi-Timeframe Score (weight: 0.15 of GS)
        trend_4h = indicators.get('trend_4h', '?')
        trend_1h = 'UP' if ema9 > ema21 else 'DOWN'
        
        mtf_map = {
            ('UP', 'UP'): 1.0,
            ('UP', 'DOWN'): 0.3,    # pullback in uptrend
            ('DOWN', 'DOWN'): -1.0,
            ('DOWN', 'UP'): -0.3,   # bounce in downtrend
        }
        s_mtf = mtf_map.get((trend_4h, trend_1h), 0.0)
        if trend_4h == '?' and trend_1h:
            s_mtf = 0.5 if trend_1h == 'UP' else -0.5
        
        # E. Core Macro Score (weight: 0.10 of GS)
        dom = indicators.get('dominance', {})
        macro_signal = dom.get('signal', 'NEUTRAL') if dom else 'NEUTRAL'
        dom_map = {'BULLISH': 0.5, 'BEARISH': -0.5, 'MIXED': 0.0, 'NEUTRAL': 0.0}
        s_dom = dom_map.get(macro_signal, 0.0)
        
        # GS Base Calculation
        W_gs = {'momentum': 0.30, 'structure': 0.25, 'orderflow': 0.20, 'mtf': 0.15, 'macro': 0.10}
        s_gs = (
            W_gs['momentum'] * s_momentum +
            W_gs['structure'] * s_structure +
            W_gs['orderflow'] * s_orderflow +
            W_gs['mtf']       * s_mtf +
            W_gs['macro']     * s_dom
        )
        
        # ── 2. ML Signal (weight: 0.40) ──
        # ml_signal is expected to be between -1.0 and 1.0
        s_ml = max(min(ml_signal, 1.0), -1.0)
        
        # ── 3. Macro Engine Bias (weight: 0.10) ──
        bias_map = {'MAXIMUM DEFENSE': -0.8, 'DEFENSE': -0.5, 'RISK ON': 0.5, 'MAXIMUM RISK': 0.8, 'NEUTRAL': 0.0}
        s_macro_bias = bias_map.get(macro_bias, 0.0)
        
        # ── Final Blended Composite Score ──
        composite = 0.50 * s_gs + 0.40 * s_ml + 0.10 * s_macro_bias
        composite = max(min(composite, 1.0), -1.0)
        
        # Direction from score
        if composite > 0:
            direction = "LONG"
        elif composite < 0:
            direction = "SHORT"
        else:
            direction = "NONE"
        
        return {
            'composite': round(composite, 3),
            'direction': direction,
            'in_trade_zone': abs(composite) >= self.NO_TRADE_ZONE,
            'components': {
                'gs_base': round(s_gs, 3),
                'ml_signal': round(s_ml, 3),
                'macro_bias': round(s_macro_bias, 3),
                'gs_momentum': round(s_momentum, 3),
                'gs_structure': round(s_structure, 3),
                'gs_orderflow': round(s_orderflow, 3),
                'gs_mtf': round(s_mtf, 3),
                'gs_dom': round(s_dom, 3),
            }
        }
    
    def _detect_market_regime(self, closes: List[float], highs: List[float],
                              lows: List[float]) -> str:
        """كشف نظام السوق: Trending / Ranging / Volatile"""
        if len(closes) < 20:
            return "UNKNOWN"
        atr_val  = TA.atr(highs, lows, closes, 14)
        atr_pct  = atr_val / closes[-1] if closes[-1] else 0
        ema_fast = TA.ema(closes, 9)
        ema_slow = TA.ema(closes, 21)
        rsi_val  = TA.rsi(closes, 14)

        if atr_pct > 0.015:                          # تقلب عالٍ > 1.5%
            return "VOLATILE"
        if ema_fast > ema_slow * 1.002 and rsi_val > 55:
            return "TRENDING_UP"
        if ema_fast < ema_slow * 0.998 and rsi_val < 45:
            return "TRENDING_DOWN"
        return "RANGING"

    def _atr_position_size(self, price: float, atr: float,
                           base_leverage: int = LEVERAGE) -> int:
        """حساب الرافعة الفعلية بناءً على ATR (تخفيض الرافعة عند التقلب العالي)"""
        if price <= 0 or atr <= 0:
            return base_leverage
        atr_pct = atr / price
        if atr_pct > 0.01:      # ATR > 1% → رافعة 10x
            return 10
        if atr_pct > 0.005:     # ATR > 0.5% → رافعة 15x
            return 15
        return base_leverage     # الافتراضي
    
    async def _fetch_market_dominance(self) -> Dict[str, Any]:
        """
        📊 Fetch macro dominance data: BTC.D, USDT.D, TOTAL3
        Source: CoinGecko /api/v3/global (free, no API key)
        Cached 5 min to avoid rate limits.
        """
        now = time.time()
        if hasattr(self, '_dominance_cache') and now - self._dominance_cache_time < 300:
            return self._dominance_cache
        
        result = {
            'btc_d': None,    # BTC Dominance %
            'usdt_mcap': None,  # USDT market cap
            'total_mcap': None, # Total crypto market cap
            'total3': None,   # Market cap ex BTC/ETH
            'usdt_d': None,   # USDT Dominance %
            'signal': 'NEUTRAL',
            'interpretation': ''
        }
        
        try:
            import requests
            resp = requests.get(
                'https://api.coingecko.com/api/v3/global',
                timeout=10,
                headers={'accept': 'application/json'}
            )
            if resp.status_code == 200:
                data = resp.json().get('data', {})
                
                # BTC Dominance
                btc_d = data.get('market_cap_percentage', {}).get('btc', 0)
                result['btc_d'] = round(btc_d, 2)
                
                # Total market cap (USD)
                total_mcap = data.get('total_market_cap', {}).get('usd', 0)
                result['total_mcap'] = total_mcap
                
                # USDT market cap from stablecoins or approximate
                # CoinGecko global doesn't give USDT directly, but gives market_cap_percentage
                usdt_pct = data.get('market_cap_percentage', {}).get('usdt', 0)
                result['usdt_d'] = round(usdt_pct, 2)
                result['usdt_mcap'] = total_mcap * (usdt_pct / 100) if usdt_pct else None
                
                # TOTAL3 = Total - BTC - ETH
                btc_mcap = total_mcap * (btc_d / 100) if btc_d else 0
                eth_pct = data.get('market_cap_percentage', {}).get('eth', 0)
                eth_mcap = total_mcap * (eth_pct / 100) if eth_pct else 0
                result['total3'] = total_mcap - btc_mcap - eth_mcap
                
                # Market cap change 24h
                result['mcap_change_24h'] = data.get('market_cap_change_percentage_24h_usd', 0)
                
                # Interpret signals
                result['signal'], result['interpretation'] = self._interpret_dominance(result)
                
                logger.info(
                    f"  🌐 [MACRO] BTC.D: {result['btc_d']}% | "
                    f"USDT.D: {result['usdt_d']}% | "
                    f"TOTAL3: ${result['total3']/1e9:.1f}B | "
                    f"Signal: {result['signal']}"
                )
            else:
                logger.warning(f"  ⚠️ CoinGecko API: {resp.status_code}")
        except Exception as e:
            logger.warning(f"  ⚠️ Dominance fetch error: {e}")
        
        self._dominance_cache = result
        self._dominance_cache_time = now
        return result
    
    def _interpret_dominance(self, dom: Dict) -> tuple:
        """
        📊 Interpret dominance signals for trading direction
        
        Rules:
        - USDT.D ↑ = money leaving crypto = BEARISH for all
        - USDT.D ↓ = money entering crypto = BULLISH for all
        - BTC.D ↑ = money flowing to BTC from alts = BEARISH for alts
        - BTC.D ↓ = altcoin season = BULLISH for alts
        - TOTAL3 ↑ = altcoins pumping = BULLISH for alts
        - TOTAL3 ↓ = altcoins dumping = BEARISH for alts
        """
        usdt_d = dom.get('usdt_d', 0)
        btc_d = dom.get('btc_d', 0)
        mcap_change = dom.get('mcap_change_24h', 0)
        
        signals = []
        
        # USDT Dominance signals
        if usdt_d and usdt_d > 5.5:
            signals.append('BEARISH (USDT.D عالي — أموال خارج الكريبتو)')
        elif usdt_d and usdt_d < 4.0:
            signals.append('BULLISH (USDT.D منخفض — أموال داخل الكريبتو)')
        
        # BTC Dominance signals for alts
        if btc_d and btc_d > 58:
            signals.append('BEARISH للألتكوين (BTC.D عالي — موسم بيتكوين)')
        elif btc_d and btc_d < 50:
            signals.append('BULLISH للألتكوين (BTC.D منخفض — موسم ألتكوين)')
        
        # Market cap momentum
        if mcap_change > 2:
            signals.append('BULLISH (السوق الكلي صاعد)')
        elif mcap_change < -2:
            signals.append('BEARISH (السوق الكلي هابط)')
        
        if not signals:
            return 'NEUTRAL', 'لا إشارات ماكرو واضحة'
        
        # Determine overall signal
        bullish = sum(1 for s in signals if 'BULLISH' in s)
        bearish = sum(1 for s in signals if 'BEARISH' in s)
        
        if bullish > bearish:
            return 'BULLISH', ' | '.join(signals)
        elif bearish > bullish:
            return 'BEARISH', ' | '.join(signals)
        else:
            return 'MIXED', ' | '.join(signals)

    async def run_advanced_analysis(self) -> Dict[str, Any]:
        """الدورة الرئيسية v5: جلب → أنماط → MTF → نظام السوق → Drawdown → Brain"""
        self._cycle_count += 1
        logger.info("🦅 NOOGH Sovereign Trading cycle starting...")

        # 1. Fetch prices
        prices = await self.fetcher.fetch_ticker(SYMBOLS)
        if not prices:
            logger.warning("⚠️ لا توجد بيانات سوق")
            return {"status": "no_data"}

        # Update active trades (includes Trailing SL)
        self.trade_mgr.update_prices(prices)
        
        # GS: Track last loss time for cooldown
        for t in self.trade_mgr.active_trades:
            if t.status == "CLOSED" and t.pnl_percent < 0 and hasattr(t, 'closed_at') and t.closed_at:
                self._last_loss_time = max(self._last_loss_time, t.closed_at)

        # ── Drawdown Guard ──
        if self.trade_mgr.is_paused():
            return {"status": "drawdown_pause", "prices": prices}

        # ═══════ Phase 4: Macro & Portfolio ═══════
        
        # 1. Macro Regime Check
        regime_data = self.macro_engine.detect_regime()
        self._current_regime = regime_data.get('regime', 'UNKNOWN')
        self._regime_directive = regime_data.get('directive', 'NEUTRAL')
        
        # Dynamic Risk Adjustment
        if self._current_regime == "STAGFLATION":
            self.MAX_CONCURRENT_POSITIONS = 1
            max_leverage = 3
        elif self._current_regime in ["OVERHEAT", "DEFLATION"]:
            self.MAX_CONCURRENT_POSITIONS = 2
            max_leverage = 5
        else:
            self.MAX_CONCURRENT_POSITIONS = 3
            max_leverage = 10
            
        logger.info(f"🌍 [MACRO] Regime: {self._current_regime} | Risk Level: {self.MAX_CONCURRENT_POSITIONS} positions max")
        
        # 2. Portfolio Allocation (HRP)
        if self._cycle_count % 12 == 1:  # Update weights every ~6 hours
            logger.info("⚖️ [PORTFOLIO] Updating HRP Allocations...")
            # We use fake recent return data for speed, or actual data if data_pipeline is running
            # For this live daemon, we'll fetch exactly 60 days of 1d data once
            from portfolio_optimizer import fetch_returns
            import numpy as np
            try:
                R, names = fetch_returns(SYMBOLS, interval='1d', days=60)
                if R.shape[0] > 0:
                    hrp_res = self.hrp_optimizer.optimize(R, names)
                    weights = hrp_res['weights']
                    self._portfolio_weights = {n: float(weights[i]) for i, n in enumerate(names)}
                    logger.info(f"   ✅ [HRP] Allocations updated: {', '.join([f'{k}: {v*100:.1f}%' for k,v in self._portfolio_weights.items() if v > 0.05])}")
            except Exception as e:
                logger.error(f"   ❌ [HRP] Failed: {e}")

        # 3. Update ML Signals
        if time.time() - self._last_ml_train_time > 3600:  # Train hourly
            logger.info("🧠 [ML] Retraining prediction models...")
            for sym in SYMBOLS:
                # Only train if we have portfolio weight (save compute)
                if self._portfolio_weights.get(sym, 1.0) < 0.01:
                    continue
                try:
                    data = ml_fetch_klines(sym, interval='1h', days=30)
                    if len(data['close']) > 100:
                        res = self.ml_pipeline.run(data)
                        self._ml_signals[sym] = res['latest_signal']
                except Exception as e:
                    logger.error(f"   ❌ [ML] Failed for {sym}: {e}")
            self._last_ml_train_time = time.time()

        # 2. Fetch macro dominance (BTC.D, USDT.D, TOTAL3) (Legacy)
        dominance = await self._fetch_market_dominance()

        # 3. For each symbol: fetch data, compute indicators, ask Brain
        decisions = []

        for symbol in SYMBOLS:
            if symbol not in prices:
                continue

            price = prices[symbol]

            # Track history
            if symbol not in self.price_history:
                self.price_history[symbol] = []
            self.price_history[symbol].append(price)
            if len(self.price_history[symbol]) > 500:
                self.price_history[symbol] = self.price_history[symbol][-500:]

            # Skip if already have active trade for this symbol
            if self.trade_mgr.get_active_count(symbol) > 0:
                active = [t for t in self.trade_mgr.active_trades
                         if t.decision.symbol == symbol and t.status == "OPEN"][0]
                elapsed = (time.time() - active.opened_at) / 60
                logger.info(
                    f"  ⏳ {symbol}: صفقة نشطة {active.decision.direction} | "
                    f"P&L: {active.pnl_percent:+.2f}% | "
                    f"متبقي: {active.decision.duration_min - elapsed:.0f} دقيقة"
                )
                continue

            # Fetch detailed data (3 timeframes)
            stats_24h  = await self.fetcher.fetch_24h(symbol)
            klines_1h  = await self.fetcher.fetch_klines(symbol, "1h", 20)
            klines_4h  = await self.fetcher.fetch_klines(symbol, "4h", 20)
            klines_5m  = await self.fetcher.fetch_klines(symbol, "5m", 50)

            # Build arrays from klines
            closes  = [k["close"]  for k in klines_5m] if klines_5m else self.price_history[symbol]
            highs   = [k["high"]   for k in klines_5m] if klines_5m else closes
            lows    = [k["low"]    for k in klines_5m] if klines_5m else closes
            volumes = [k["volume"] for k in klines_5m] if klines_5m else []

            closes_4h = [k["close"] for k in klines_4h] if klines_4h else closes
            highs_4h  = [k["high"]  for k in klines_4h] if klines_4h else highs
            lows_4h   = [k["low"]   for k in klines_4h] if klines_4h else lows

            if len(closes) < 5:
                logger.info(f"  ⏳ {symbol}: بيانات غير كافية ({len(closes)} شموع)")
                continue

            # ── Technical Indicators (5m) ──
            rsi      = TA.rsi(closes, 14)
            ema_9    = TA.ema(closes, 9)
            ema_21   = TA.ema(closes, 21)
            sma_50   = TA.sma(closes, 50)
            bb_upper, bb_mid, bb_lower = TA.bollinger(closes, 20)
            macd_line, macd_sig, macd_hist = TA.macd(closes)
            atr      = TA.atr(highs, lows, closes, 14)
            vol_prof = TA.volume_profile(volumes) if volumes else "UNKNOWN"

            # ── Multi-Timeframe (4h) ──
            rsi_4h   = TA.rsi(closes_4h, 14) if len(closes_4h) >= 15 else None
            ema9_4h  = TA.ema(closes_4h, 9)  if len(closes_4h) >= 9  else None
            ema21_4h = TA.ema(closes_4h, 21) if len(closes_4h) >= 21 else None
            trend_4h = ("UP" if (ema9_4h and ema21_4h and ema9_4h > ema21_4h) else
                        "DOWN" if (ema9_4h and ema21_4h) else "?")

            # ── Candle Patterns (1h) ──
            candle_patterns = CandlePatterns.detect(klines_1h) if len(klines_1h) >= 3 else ["بيانات غير كافية"]

            # ── v8: Professional Analysis ──
            # Order Book Depth
            order_book = await self.fetcher.fetch_order_book(symbol)
            
            # Support/Resistance (from 1h klines — more reliable than 5m)
            sr_levels = MarketDataFetcher.detect_support_resistance(klines_1h)
            
            # Market Structure (from 1h klines)
            mkt_structure = MarketDataFetcher.detect_market_structure(klines_1h)

            # ── Market Regime ──
            regime = self._detect_market_regime(closes, highs, lows)

            # ── ATR-based Position Sizing ──
            effective_leverage = self._atr_position_size(price, atr)

            indicators = {
                "rsi": rsi, "ema_9": ema_9, "ema_21": ema_21,
                "sma_50": sma_50, "bb_upper": bb_upper, "bb_mid": bb_mid,
                "bb_lower": bb_lower, "macd": macd_line, "macd_signal": macd_sig,
                "macd_hist": macd_hist, "atr": atr,
                "volume_profile": vol_prof,
                "change_24h": stats_24h.get("change_24h", 0),
                # جديد v5
                "candle_patterns": candle_patterns,
                "market_regime":   regime,
                "rsi_4h":          rsi_4h,
                "ema9_4h":         ema9_4h,
                "trend_4h":        trend_4h,
                # v7: macro dominance
                "dominance":       dominance,
                # v8: professional analysis
                "order_book":      order_book,
                "sr_levels":       sr_levels,
                "mkt_structure":   mkt_structure,
            }

            klines_text = self.fetcher.format_klines(klines_1h)

            logger.info(
                f"  📊 {symbol} | نظام: {regime} | "
                f"أنماط: {candle_patterns[0][:30]} | "
                f"رافعة فعلية: {effective_leverage}x"
            )

            # ── v6: فلاتر الأنظمة المُولَّدة ذاتياً ──

            # 1. فلتر معدل التمويل (FundingRateFilter)
            if self._funding_filter:
                import asyncio
                try:
                    # نستخدم معدل افتراضي مؤقت (يمكن لاحقاً ربطه بـ Binance futures API)
                    mock_funding_rate = 0.0001  # 0.01% — neutral
                    funding_ok = asyncio.get_event_loop().run_until_complete(
                        self._funding_filter.should_trade(mock_funding_rate)
                    ) if not asyncio.get_event_loop().is_running() else True
                    if not funding_ok:
                        logger.info(f"  🚫 [{symbol}] FundingRateFilter: معدل تمويل مرتفع — تجاوز")
                        continue
                except Exception:
                    pass  # لا نوقف التداول إذا فشل الفلتر

            # 2. حارس ارتباط BTC (BtcCorrelationGuard)
            if self._btc_guard and symbol != "BTCUSDT":
                try:
                    signal_check = self._btc_guard.apply_guard({"symbol": symbol})
                    if signal_check is None:
                        logger.info(f"  🚫 [{symbol}] BtcCorrelationGuard: ارتباط عالٍ مع BTC — تجاوز")
                        continue
                except Exception:
                    pass

            # 3. تسجيل نقاط الأنماط وإضافتها للمؤشرات
            pattern_score = 0.5  # افتراضي محايد
            if self._pattern_scorer and candle_patterns:
                try:
                    first_pattern = candle_patterns[0] if candle_patterns else ""
                    # تطابق الأنماط المعروفة فقط
                    known = {"Doji", "Hammer", "Engulfing", "Morning Star", "Evening Star", "Marubozu"}
                    for p in candle_patterns:
                        for k in known:
                            if k in p:
                                pattern_score = self._pattern_scorer.get_pattern_score(k)
                                break
                    indicators["pattern_score"] = pattern_score
                    logger.info(f"  🎯 [{symbol}] PatternScore: {pattern_score:.2f}")
                except Exception:
                    pass

            # ═══════ GS Phase 1: Pre-Brain Quantitative Filters ═══════
            
            # Daily reset
            today = datetime.now().strftime('%Y-%m-%d')
            if today != self._daily_reset_date:
                self._daily_trade_count = 0
                self._daily_reset_date = today
            
            # Check 1: Daily trade limit
            if self._daily_trade_count >= self.MAX_DAILY_TRADES:
                logger.info(f"  🚫 [{symbol}] Daily limit reached ({self._daily_trade_count}/{self.MAX_DAILY_TRADES})")
                continue
            
            # Check 2: Max concurrent positions
            total_active = self.trade_mgr.get_active_count()
            if total_active >= self.MAX_CONCURRENT_POSITIONS:
                logger.info(f"  🚫 [{symbol}] Max positions reached ({total_active}/{self.MAX_CONCURRENT_POSITIONS})")
                continue
            
            # Check 3: Loss cooldown
            if self._last_loss_time and (time.time() - self._last_loss_time) < self.LOSS_COOLDOWN_SEC:
                remaining = self.LOSS_COOLDOWN_SEC - (time.time() - self._last_loss_time)
                logger.info(f"  ⏸️ [{symbol}] Cooldown: {remaining:.0f}s remaining after loss")
                continue
            
            # ═══════ Phase 4: Portfolio Filter ═══════
            weight = self._portfolio_weights.get(symbol, 1.0)  # Default 1.0 if not allocated yet
            if weight < 0.01 and self._portfolio_weights:
                logger.info(f"  🚫 [{symbol}] Portfolio Filter: Allocation {weight*100:.1f}% is below 1% threshold")
                continue

            # ═══════ Phase 4: Blended Composite Score ═══════
            ml_pred = self._ml_signals.get(symbol, 0.0)
            score_data = self.compute_composite_score(indicators, ml_signal=ml_pred, macro_bias=self._regime_directive)
            composite = score_data['composite']
            score_dir = score_data['direction']
            in_zone = score_data['in_trade_zone']
            comps = score_data['components']
            
            logger.info(
                f"  📐 [{symbol}] Final Score: {composite:+.3f} ({score_dir}) | "
                f"GS Base: {comps['gs_base']:+.2f} | ML: {comps['ml_signal']:+.2f} | Macro: {comps['macro_bias']:+.2f} | "
                f"HRP Weight: {weight*100:.1f}%"
            )
            
            # Check 5: No-trade zone
            if not in_zone:
                logger.info(f"  🚫 [{symbol}] NO-TRADE ZONE: |{composite:.3f}| < {self.NO_TRADE_ZONE}")
                continue

            # 3. Ask Brain for decision (only if composite score allows)
            decision = await self.brain.analyze(symbol, price, indicators, klines_text)
            
            # GS: Override Brain direction if it conflicts with composite score
            if decision and decision.direction != score_dir:
                logger.info(
                    f"  🔄 [{symbol}] Brain says {decision.direction} but Composite says {score_dir} "
                    f"(score={composite:+.3f}) — using Composite direction"
                )
                decision.direction = score_dir
            
            # GS: Scale Brain confidence by composite magnitude
            if decision:
                score_magnitude = abs(composite)
                decision.confidence = min(decision.confidence * (0.7 + 0.3 * score_magnitude / 1.0), 0.95)

            # v7: Adjusted thresholds — compound growth needs trades to compound
            MIN_CONFIDENCE = 0.55
            if regime == "RANGING":
                MIN_CONFIDENCE = 0.60   # سوق متذبذب — ثقة معقولة
            elif regime == "VOLATILE":
                MIN_CONFIDENCE = 0.70   # تقلب عالي — حذر أكثر
            # v6: أنماط ضعيفة تاريخياً → رفع العتبة
            # Only penalize truly weak patterns (< 0.3), not "unknown" (0.5)
            if pattern_score < 0.3:
                MIN_CONFIDENCE = min(MIN_CONFIDENCE + 0.05, 0.85)
                logger.info(f"  📉 [{symbol}] نمط ضعيف (score={pattern_score:.2f}) → عتبة {MIN_CONFIDENCE:.0%}")

            if decision and decision.confidence >= MIN_CONFIDENCE:
                # ====== v9: Quality Filters — improve win rate ======
                
                # Filter 1: MTF Alignment Veto
                # Don't SHORT if 4h trend is UP, don't LONG if 4h trend is DOWN
                if trend_4h == "UP" and decision.direction == "SHORT":
                    logger.info(f"  🚫 [{symbol}] MTF VETO: SHORT رُفض — 4h trend UP")
                    continue
                elif trend_4h == "DOWN" and decision.direction == "LONG":
                    logger.info(f"  🚫 [{symbol}] MTF VETO: LONG رُفض — 4h trend DOWN")
                    continue
                
                # Filter 2: Structure Alignment
                # Reduce confidence if direction conflicts with market structure
                struct = mkt_structure.get('structure', '') if mkt_structure else ''
                if decision.direction == "LONG" and struct in ("BEARISH_STRUCTURE", "DESCENDING_TRIANGLE"):
                    decision.confidence *= 0.85
                    logger.info(f"  ⚠️ [{symbol}] Structure conflict: LONG vs {struct} → ثقة {decision.confidence:.0%}")
                    if decision.confidence < MIN_CONFIDENCE:
                        logger.info(f"  🚫 [{symbol}] ثقة منخفضة بعد فلتر الهيكل — لا صفقة")
                        continue
                elif decision.direction == "SHORT" and struct in ("BULLISH_STRUCTURE", "ASCENDING_TRIANGLE"):
                    decision.confidence *= 0.85
                    logger.info(f"  ⚠️ [{symbol}] Structure conflict: SHORT vs {struct} → ثقة {decision.confidence:.0%}")
                    if decision.confidence < MIN_CONFIDENCE:
                        logger.info(f"  🚫 [{symbol}] ثقة منخفضة بعد فلتر الهيكل — لا صفقة")
                        continue
                
                # Filter 3: Max SL cap (2.5%) — prevent huge losses
                if decision.stop_loss and decision.entry_price:
                    sl_dist_pct = abs(decision.entry_price - decision.stop_loss) / decision.entry_price
                    if sl_dist_pct > 0.025:
                        # Cap SL at 2.5%
                        if decision.direction == "LONG":
                            decision.stop_loss = decision.entry_price * (1 - 0.025)
                        else:
                            decision.stop_loss = decision.entry_price * (1 + 0.025)
                        logger.info(f"  🔒 [{symbol}] SL capped: {sl_dist_pct:.1%} → 2.5%")
                
                logger.info(f"  ✅ [{symbol}] قرار مقبول: {decision.direction} ثقة {decision.confidence:.0%}")

                decision.leverage = effective_leverage
                decisions.append(decision)
                self.trade_mgr.open_trade(decision)
                self._daily_trade_count += 1
            elif decision:
                logger.info(
                    f"  ⚠️ {symbol}: {decision.direction} "
                    f"ثقة {decision.confidence:.0%} < {MIN_CONFIDENCE:.0%} "
                    f"({regime}) — لا صفقة"
                )
        
        # === DISPLAY ===
        logger.info("═" * 62)
        logger.info(f"  🦅 NOOGH SOVEREIGN TRADING | {datetime.now().strftime('%H:%M:%S')}")
        logger.info("═" * 62)
        
        for symbol in SYMBOLS:
            if symbol not in prices:
                continue
            p = prices[symbol]
            change = ""
            hist = self.price_history.get(symbol, [])
            if len(hist) > 1:
                ch = (hist[-1] - hist[-2]) / hist[-2] * 100
                change = f"{'🟢' if ch > 0 else '🔴'} {ch:+.3f}%"
            logger.info(f"  💰 {symbol:8} ${p:>12,.2f}  {change}")
        
        # Active trades
        if self.trade_mgr.active_trades:
            logger.info("─" * 62)
            logger.info("  📊 الصفقات النشطة:")
            for t in self.trade_mgr.active_trades:
                if t.status != "OPEN": continue
                d = t.decision
                elapsed = (time.time() - t.opened_at) / 60
                remaining = d.duration_min - elapsed
                pnl_icon = "🟢" if t.pnl_percent > 0 else "🔴"
                logger.info(
                    f"    {d.icon} {d.symbol} {d.direction} {d.leverage}x | "
                    f"P&L: {pnl_icon}{t.pnl_percent:+.2f}% | "
                    f"⏱️ {remaining:.0f}m | "
                    f"TPs: {[f'${tp:,.2f}' for tp in d.take_profits]} SL: ${d.stop_loss:,.2f}"
                )
        
        # New decisions
        if decisions:
            logger.info(f"  ⚡ تم اتخاذ {len(decisions)} قرار(ات) بالتداول")
        else:
            logger.info("  💤 لا توجد قرارات جديدة")
            
        # ═══════ Phase 4: Stat-Arb Subroutine (ETH/SOL) ═══════
        if 'ETHUSDT' in prices and 'SOLUSDT' in prices and self._cycle_count % 5 == 1:
            try:
                logger.info("⚖️ [STAT-ARB] Syncing ETH/SOL spread...")
                y1 = np.array(self.price_history.get('ETHUSDT', []))
                y2 = np.array(self.price_history.get('SOLUSDT', []))
                if len(y1) > 50 and len(y2) > 50:
                    n = min(len(y1), len(y2))
                    coint = engle_granger_coint(y1[:n], y2[:n])
                    if coint['is_cointegrated']:
                        config = PairConfig('ETHUSDT', 'SOLUSDT', coint['beta'], coint['alpha'], entry_z=2.0)
                        engine = ZScoreEngine(config)
                        signals, spreads, zs = engine.generate_signals(y1[:n], y2[:n])
                        current_z = zs[-1]
                        logger.info(f"   ✅ [STAT-ARB] ETH/SOL Z-Score: {current_z:+.2f} | Cointegrated: Yes")
                        
                        if current_z > 2.0:
                            self.trade_mgr.open_pair_trade("ETHUSDT/SOLUSDT", "SHORT_SPREAD", current_z)
                        elif current_z < -2.0:
                            self.trade_mgr.open_pair_trade("ETHUSDT/SOLUSDT", "LONG_SPREAD", current_z)
                    else:
                        logger.info("   ⚠️ [STAT-ARB] ETH/SOL Cointegration broken temporarily.")
            except Exception as e:
                logger.error(f"   ❌ [STAT-ARB] Subroutine failed: {e}")

        # New decisions (continue displaying)
        if decisions:
            logger.info("─" * 62)
            logger.info("  🧠 قرارات الدماغ الجديدة:")
            for d in decisions:
                logger.info(
                    f"  ▶️ {d.icon} {d.symbol:8} {d.direction:5} @ ${d.entry_price:,.2f} | "
                    f"TPs: {[f'${tp:,.2f}' for tp in d.take_profits]} SL: ${d.stop_loss:,.2f}"
                )
                logger.info(f"    💬 {d.reasoning[:80]}")
        
        # Stats
        s = self.trade_mgr.stats
        if s["total"] > 0:
            wr = (s["wins"] / s["total"] * 100) if s["total"] > 0 else 0
            logger.info("─" * 62)
            logger.info(
                f"  📈 الإحصائيات: {s['total']} صفقة | "
                f"✅{s['wins']} ❌{s['losses']} | "
                f"WR: {wr:.0f}% | "
                f"P&L: {s['total_pnl']:+.2f}%"
            )
        
        logger.info("═" * 62)
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "prices": prices,
            "decisions": [
                {
                    "symbol": d.symbol, "direction": d.direction,
                    "confidence": d.confidence, "entry": d.entry_price,
                    "tp": d.take_profits, "sl": d.stop_loss,
                    "reasoning": d.reasoning
                }
                for d in decisions
            ],
            "active_trades": len(self.trade_mgr.active_trades),
            "stats": self.trade_mgr.stats
        }


if __name__ == "__main__":
    async def test():
        class DummyBrain:
            async def analyze(self, symbol, price, indicators, klines_text):
                from unified_core.noogh_wisdom import TradeDecision
                tp1 = price * 1.01
                tp2 = price * 1.03
                tp3 = price * 1.05
                return TradeDecision(symbol=symbol, direction="LONG", entry_price=price, 
                                   take_profits=[tp1, tp2, tp3], stop_loss=price*0.95, 
                                   leverage=5, confidence=0.8, reasoning="Test output")
                               
        wisdom = AdvancedNooghWisdom()
        wisdom.brain = DummyBrain()
        result = await wisdom.run_advanced_analysis()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    asyncio.run(test())
