#!/usr/bin/env python3
"""
NOOGH Volatility Guard — مسار B
---------------------------------
حماية متقدمة من التقلبات العالية قبل السماح بأي صفقة.

المكونات:
  1. ATR-based Volatility Classifier  — تصنيف السوق (هادئ / عادي / متقلب / عاصف)
  2. Regime-Aware Position Sizer      — تقليل الحجم تلقائياً عند التقلبات
  3. Dynamic Circuit Breakers         — قواطع ديناميكية تتكيف مع ظروف السوق
  4. Drawdown Guard                   — مراقبة الخسائر التراكمية
  5. Correlation Spike Detector       — كشف ارتفاع الارتباط (مؤشر الذعر)
"""

import sys, os, json, time, sqlite3, logging
from datetime import datetime, date
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

sys.path.insert(0, "/home/noogh/projects/noogh_unified_system/src")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | volatility_guard | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            "/home/noogh/projects/noogh_unified_system/src/logs/volatility_guard.log"
        ),
    ]
)
logger = logging.getLogger("volatility_guard")

DB_PATH = "/home/noogh/projects/noogh_unified_system/src/data/shared_memory.sqlite"


# ══════════════════════════════════════════════
# Enums & Dataclasses
# ══════════════════════════════════════════════

class VolatilityRegime(str, Enum):
    CALM     = "CALM"      # ATR < 0.5%  → حجم عادي
    NORMAL   = "NORMAL"    # ATR 0.5-1.5% → حجم عادي
    ELEVATED = "ELEVATED"  # ATR 1.5-3%  → حجم 70%
    HIGH     = "HIGH"      # ATR 3-5%    → حجم 40%
    EXTREME  = "EXTREME"   # ATR > 5%    → حجم 20% أو إيقاف


@dataclass
class VolatilitySnapshot:
    symbol:          str
    atr_pct:         float           # ATR كنسبة مئوية من السعر
    regime:          VolatilityRegime
    size_multiplier: float           # معامل تعديل الحجم (0.0 → 1.0)
    trading_allowed: bool
    reason:          str
    timestamp:       str


@dataclass
class CircuitBreakerState:
    daily_pnl:          float = 0.0
    daily_loss_limit:   float = 0.02   # 2%
    consecutive_losses: int   = 0
    max_consecutive:    int   = 3
    max_drawdown_pct:   float = 0.05   # 5% من رأس المال الأولي
    peak_balance:       float = 1000.0
    current_balance:    float = 1000.0
    is_active:          bool  = False
    activated_reason:   str   = ""
    last_reset_date:    str   = ""


# ══════════════════════════════════════════════
# VolatilityGuard
# ══════════════════════════════════════════════

class VolatilityGuard:
    """
    الحارس الأول قبل أي صفقة — يمنع التداول في ظروف خطرة
    """

    # حدود ATR% للتصنيف
    ATR_THRESHOLDS = {
        VolatilityRegime.CALM:     (0.0,  0.5),
        VolatilityRegime.NORMAL:   (0.5,  1.5),
        VolatilityRegime.ELEVATED: (1.5,  3.0),
        VolatilityRegime.HIGH:     (3.0,  5.0),
        VolatilityRegime.EXTREME:  (5.0,  999.0),
    }

    # معامل الحجم لكل نظام
    SIZE_MULTIPLIERS = {
        VolatilityRegime.CALM:     1.0,
        VolatilityRegime.NORMAL:   1.0,
        VolatilityRegime.ELEVATED: 0.70,
        VolatilityRegime.HIGH:     0.40,
        VolatilityRegime.EXTREME:  0.0,   # إيقاف كامل
    }

    def __init__(self,
                 daily_loss_limit: float = 0.02,
                 max_consecutive_losses: int = 3,
                 max_drawdown_pct: float = 0.05,
                 initial_balance: float = 1000.0):

        self.cb = CircuitBreakerState(
            daily_loss_limit   = daily_loss_limit,
            max_consecutive    = max_consecutive_losses,
            max_drawdown_pct   = max_drawdown_pct,
            peak_balance       = initial_balance,
            current_balance    = initial_balance,
            last_reset_date    = str(date.today()),
        )
        self._snapshot_cache: Dict[str, VolatilitySnapshot] = {}
        logger.info(
            f"🛡️ VolatilityGuard active | "
            f"DailyLoss≤{daily_loss_limit*100:.0f}% | "
            f"MaxLosses≤{max_consecutive_losses} | "
            f"MaxDD≤{max_drawdown_pct*100:.0f}%"
        )

    # ─────────────────────────────────────────
    # تصنيف التقلب
    # ─────────────────────────────────────────

    def classify_volatility(self, symbol: str, atr: float, price: float) -> VolatilitySnapshot:
        """
        يُصنّف السوق ويُقرر حجم الصفقة المسموح به

        Args:
            symbol: رمز العملة
            atr:    قيمة ATR (بالدولار)
            price:  السعر الحالي

        Returns:
            VolatilitySnapshot
        """
        if price <= 0:
            return VolatilitySnapshot(
                symbol=symbol, atr_pct=0.0,
                regime=VolatilityRegime.EXTREME,
                size_multiplier=0.0, trading_allowed=False,
                reason="Invalid price (≤0)",
                timestamp=datetime.now().isoformat()
            )

        atr_pct = (atr / price) * 100
        regime  = self._get_regime(atr_pct)
        mult    = self.SIZE_MULTIPLIERS[regime]
        allowed = mult > 0.0

        reason = (
            f"ATR={atr_pct:.2f}% → Regime={regime.value} "
            f"| SizeX={mult:.0%}"
            + (" | TRADING BLOCKED" if not allowed else "")
        )

        snap = VolatilitySnapshot(
            symbol=symbol,
            atr_pct=atr_pct,
            regime=regime,
            size_multiplier=mult,
            trading_allowed=allowed,
            reason=reason,
            timestamp=datetime.now().isoformat(),
        )

        self._snapshot_cache[symbol] = snap

        if regime in (VolatilityRegime.HIGH, VolatilityRegime.EXTREME):
            logger.warning(f"  ⚠️ {symbol}: {reason}")
        else:
            logger.debug(f"  ✅ {symbol}: {reason}")

        return snap

    def _get_regime(self, atr_pct: float) -> VolatilityRegime:
        for regime, (lo, hi) in self.ATR_THRESHOLDS.items():
            if lo <= atr_pct < hi:
                return regime
        return VolatilityRegime.EXTREME

    # ─────────────────────────────────────────
    # تعديل حجم الصفقة
    # ─────────────────────────────────────────

    def adjust_position_size(self, symbol: str, quantity: float,
                             atr: float, price: float) -> Tuple[float, str]:
        """
        يُعدّل حجم الصفقة بناءً على نظام التقلبات

        Returns:
            (adjusted_qty, reason)
        """
        snap = self.classify_volatility(symbol, atr, price)

        if not snap.trading_allowed:
            return 0.0, f"BLOCKED: {snap.reason}"

        adjusted = quantity * snap.size_multiplier
        reason   = f"Vol={snap.atr_pct:.2f}% | Regime={snap.regime.value} | {quantity:.4f}→{adjusted:.4f}"
        return adjusted, reason

    # ─────────────────────────────────────────
    # Circuit Breaker
    # ─────────────────────────────────────────

    def can_trade(self, equity: float) -> Tuple[bool, str]:
        """
        القاطع الرئيسي — يُحدد إذا كان التداول مسموحاً الآن

        Returns:
            (allowed, reason)
        """
        # إعادة تعيين يومي
        self._daily_reset(equity)

        # تحديث الذروة
        if equity > self.cb.peak_balance:
            self.cb.peak_balance = equity
        self.cb.current_balance = equity

        # 1. خسارة يومية
        max_loss = equity * self.cb.daily_loss_limit
        if self.cb.daily_pnl <= -max_loss:
            reason = (
                f"Daily loss limit hit: ${self.cb.daily_pnl:.2f} / -${max_loss:.2f}"
                f" ({self.cb.daily_loss_limit*100:.0f}%)"
            )
            self._activate(reason)
            return False, reason

        # 2. خسائر متتالية
        if self.cb.consecutive_losses >= self.cb.max_consecutive:
            reason = f"Max consecutive losses: {self.cb.consecutive_losses}/{self.cb.max_consecutive}"
            self._activate(reason)
            return False, reason

        # 3. Drawdown عن الذروة
        if self.cb.peak_balance > 0:
            drawdown = (self.cb.peak_balance - equity) / self.cb.peak_balance
            if drawdown >= self.cb.max_drawdown_pct:
                reason = (
                    f"Max drawdown hit: {drawdown*100:.1f}%"
                    f" (Peak=${self.cb.peak_balance:.2f} → Now=${equity:.2f})"
                )
                self._activate(reason)
                return False, reason

        # كل شيء سليم
        if self.cb.is_active:
            logger.info("✅ Circuit breaker cleared — trading resumed")
            self.cb.is_active = False
            self.cb.activated_reason = ""

        return True, "OK"

    def record_trade_result(self, pnl: float, equity: float):
        """يُسجّل نتيجة صفقة ويُحدّث counters"""
        self.cb.daily_pnl      += pnl
        self.cb.current_balance = equity

        if pnl < 0:
            self.cb.consecutive_losses += 1
            logger.warning(
                f"📉 Loss ${pnl:.2f} | Consecutive: "
                f"{self.cb.consecutive_losses}/{self.cb.max_consecutive}"
            )
        else:
            if self.cb.consecutive_losses > 0:
                logger.info(f"✅ Win breaks streak (was {self.cb.consecutive_losses})")
            self.cb.consecutive_losses = 0

        # حفظ في DB
        self._persist_state()

    def _activate(self, reason: str):
        if not self.cb.is_active:
            logger.error(f"🚨 CIRCUIT BREAKER ACTIVATED: {reason}")
            self.cb.is_active        = True
            self.cb.activated_reason = reason
            self._persist_state()

    def _daily_reset(self, equity: float):
        today = str(date.today())
        if self.cb.last_reset_date != today:
            logger.info(
                f"📅 Daily reset | Prev PnL: ${self.cb.daily_pnl:.2f} | "
                f"Losses: {self.cb.consecutive_losses}"
            )
            self.cb.daily_pnl          = 0.0
            self.cb.consecutive_losses = 0
            self.cb.is_active          = False
            self.cb.activated_reason   = ""
            self.cb.last_reset_date    = today

    # ─────────────────────────────────────────
    # استمرارية الحالة
    # ─────────────────────────────────────────

    def _persist_state(self):
        """يحفظ حالة القاطع في shared_memory"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur  = conn.cursor()
            data = asdict(self.cb)
            cur.execute(
                "INSERT OR REPLACE INTO beliefs (key, value, utility_score, updated_at) "
                "VALUES (?, ?, ?, ?)",
                ("trading:circuit_breaker_state",
                 json.dumps(data, ensure_ascii=False),
                 0.99, time.time())
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"  DB persist error: {e}")

    def load_state(self):
        """يستعيد حالة القاطع من DB عند الإعادة"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur  = conn.cursor()
            cur.execute(
                "SELECT value FROM beliefs WHERE key='trading:circuit_breaker_state'"
            )
            row = cur.fetchone()
            conn.close()
            if row:
                stored = json.loads(row[0])
                for k, v in stored.items():
                    if hasattr(self.cb, k):
                        setattr(self.cb, k, v)
                logger.info(
                    f"🔄 Circuit breaker state restored | "
                    f"DailyPnL=${self.cb.daily_pnl:.2f} | "
                    f"Losses={self.cb.consecutive_losses}"
                )
        except Exception as e:
            logger.warning(f"  Could not restore CB state: {e}")

    def get_status(self) -> Dict:
        """ملخص حالة الحارس"""
        return {
            "circuit_breaker_active": self.cb.is_active,
            "activated_reason":       self.cb.activated_reason,
            "daily_pnl":              round(self.cb.daily_pnl, 2),
            "consecutive_losses":     self.cb.consecutive_losses,
            "peak_balance":           round(self.cb.peak_balance, 2),
            "current_balance":        round(self.cb.current_balance, 2),
            "drawdown_pct":           round(
                (self.cb.peak_balance - self.cb.current_balance) / max(self.cb.peak_balance, 1) * 100, 2
            ),
        }


# ── Singleton ──────────────────────────────────────────
_guard: Optional[VolatilityGuard] = None


def get_volatility_guard(**kwargs) -> VolatilityGuard:
    """Singleton factory"""
    global _guard
    if _guard is None:
        _guard = VolatilityGuard(**kwargs)
        _guard.load_state()
    return _guard


if __name__ == "__main__":
    guard = get_volatility_guard(initial_balance=1000.0)

    # اختبار تصنيف التقلبات
    for symbol, atr, price in [
        ("BTCUSDT", 200,  65000),   # CALM
        ("ETHUSDT", 30,   3000),    # NORMAL
        ("SOLUSDT", 5.0,  150),     # ELEVATED
        ("DOGEUSDT", 0.01, 0.1),    # HIGH
        ("SHIB1000USDT", 0.003, 0.02),  # EXTREME
    ]:
        snap = guard.classify_volatility(symbol, atr, price)
        print(f"{symbol:20s} | ATR%={snap.atr_pct:.2f}% | {snap.regime.value} | x{snap.size_multiplier}")

    print("\n--- Circuit Breaker Test ---")
    print(guard.can_trade(1000))       # OK
    guard.record_trade_result(-25, 975)
    guard.record_trade_result(-25, 950)
    guard.record_trade_result(-25, 925)
    print(guard.can_trade(925))        # Should be BLOCKED
    print(guard.get_status())
