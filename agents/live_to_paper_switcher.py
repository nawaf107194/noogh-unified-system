#!/usr/bin/env python3
"""
NOOGH Live-to-Paper Switcher
------------------------------
مفتاح الأمان: يُحدّد متى يتحوّل النظام من Paper إلى Live
ومتى يتراجع فوراً بناءً على شروط صارمة.

يُستدعى من الـ Orchestrator في كل دورة.
"""

import sys, os, json, time, sqlite3, logging
from datetime import datetime
from typing import Dict, List

sys.path.insert(0, "/home/noogh/projects/noogh_unified_system/src")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | mode_switcher | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            "/home/noogh/projects/noogh_unified_system/src/logs/mode_switcher.log"
        ),
    ]
)
logger = logging.getLogger("mode_switcher")

SRC     = "/home/noogh/projects/noogh_unified_system/src"
DB_PATH = f"{SRC}/data/shared_memory.sqlite"

# ── شروط التحوّل إلى LIVE ──────────────────────
LIVE_REQUIREMENTS = {
    "min_paper_trades":      50,    # لا أقل من 50 صفقة paper
    "min_win_rate":          0.60,  # Win Rate ≥ 60%
    "max_drawdown":          0.03,  # Max Drawdown < 3%
    "clean_days_required":   7,     # 7 أيام بدون circuit_breaker
    "allowed_regimes":       ["CALM", "NORMAL"],  # لا تدخل LIVE في HIGH/EXTREME
}

# ── شروط التراجع الفوري إلى PAPER ──────────────
PAPER_TRIGGERS = {
    "live_win_rate_min":     0.45,  # أقل من 45% على آخر 20 صفقة → تراجع
    "live_min_trades":       20,    # لا تحكم قبل 20 صفقة live
    "circuit_breaker_back":  True,  # أي circuit_breaker → تراجع فوري
}


class LiveToPaperSwitcher:
    """
    يُراقب أداء التداول ويُقرّر الوضع: PAPER أو LIVE.
    """

    def __init__(self):
        self._current_mode = self._load_mode()
        logger.info(f"🔄 LiveToPaperSwitcher initialized | Mode: {self._current_mode}")

    # ─────────────────────────────────────────────
    # قراءة الوضع الحالي
    # ─────────────────────────────────────────────

    def _load_mode(self) -> str:
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur  = conn.cursor()
            cur.execute(
                "SELECT value FROM beliefs WHERE key='trading:mode' LIMIT 1"
            )
            row = cur.fetchone()
            conn.close()
            if row:
                data = json.loads(row[0])
                return data.get("mode", "PAPER")
        except Exception:
            pass
        return "PAPER"

    def _save_mode(self, mode: str, reason: str):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur  = conn.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO beliefs (key, value, utility_score, updated_at) "
                "VALUES (?, ?, ?, ?)",
                ("trading:mode",
                 json.dumps({
                     "mode":         mode,
                     "reason":       reason,
                     "changed_at":   datetime.now().isoformat(),
                 }, ensure_ascii=False),
                 0.99, time.time())
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"  ❌ save_mode error: {e}")

    # ─────────────────────────────────────────────
    # جمع البيانات المطلوبة
    # ─────────────────────────────────────────────

    def _get_paper_stats(self) -> Dict:
        """إحصائيات صفقات PAPER"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur  = conn.cursor()
            # آخر 50 صفقة paper
            cur.execute(
                "SELECT pnl FROM paper_trades ORDER BY created_at DESC LIMIT 50"
            )
            rows  = cur.fetchall()
            pnls  = [r[0] for r in rows if r[0] is not None]
            total = len(pnls)
            wins  = sum(1 for p in pnls if p > 0)
            wr    = wins / total if total else 0.0

            # Max drawdown
            equity, peak, max_dd = 0.0, 0.0, 0.0
            for p in reversed(pnls):
                equity += p
                if equity > peak: peak = equity
                dd = peak - equity
                if dd > max_dd: max_dd = dd

            conn.close()
            return {"total": total, "win_rate": wr, "max_drawdown": max_dd}
        except Exception:
            return {"total": 0, "win_rate": 0.0, "max_drawdown": 0.0}

    def _get_live_stats(self) -> Dict:
        """إحصائيات آخر 20 صفقة LIVE"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur  = conn.cursor()
            cur.execute(
                "SELECT pnl FROM live_trades ORDER BY created_at DESC LIMIT 20"
            )
            rows  = cur.fetchall()
            pnls  = [r[0] for r in rows if r[0] is not None]
            total = len(pnls)
            wins  = sum(1 for p in pnls if p > 0)
            wr    = wins / total if total else 0.0
            conn.close()
            return {"total": total, "win_rate": wr}
        except Exception:
            return {"total": 0, "win_rate": 0.0}

    def _get_clean_days(self) -> int:
        """كم يوم متتالي بدون circuit_breaker"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur  = conn.cursor()
            cur.execute(
                "SELECT updated_at FROM beliefs WHERE key='trading:blocked' "
                "ORDER BY updated_at DESC LIMIT 1"
            )
            row = cur.fetchone()
            conn.close()
            if not row:
                return 99  # لم يُفعَّل قط
            last_block_ts = row[0]
            days_since = (time.time() - last_block_ts) / 86400
            return int(days_since)
        except Exception:
            return 0

    def _get_circuit_breaker_active(self) -> bool:
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur  = conn.cursor()
            cur.execute(
                "SELECT value FROM beliefs WHERE key='trading:circuit_breaker_state' LIMIT 1"
            )
            row = cur.fetchone()
            conn.close()
            if row:
                data = json.loads(row[0])
                return data.get("tripped", False)
        except Exception:
            pass
        return False

    def _get_current_regime(self) -> str:
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur  = conn.cursor()
            cur.execute(
                "SELECT value FROM beliefs WHERE key='trading:volatility_state' "
                "ORDER BY updated_at DESC LIMIT 1"
            )
            row = cur.fetchone()
            conn.close()
            if row:
                return json.loads(row[0]).get("regime", "NORMAL")
        except Exception:
            pass
        return "NORMAL"

    # ─────────────────────────────────────────────
    # منطق القرار
    # ─────────────────────────────────────────────

    def evaluate(self) -> Dict:
        """
        يُقيّم الوضع الحالي ويُقرّر PAPER أو LIVE.
        يُعيد dict بالقرار والسبب.
        """
        regime        = self._get_current_regime()
        cb_active     = self._get_circuit_breaker_active()
        paper_stats   = self._get_paper_stats()
        live_stats    = self._get_live_stats()
        clean_days    = self._get_clean_days()
        prev_mode     = self._current_mode

        logger.info(f"\n{'─'*55}")
        logger.info(f"🔄 [MODE SWITCHER] Mode الحالي: {prev_mode} | Regime: {regime}")
        logger.info(f"   Paper: {paper_stats['total']} trades | WR={paper_stats['win_rate']:.1%} | DD=${paper_stats['max_drawdown']:.2f}")
        logger.info(f"   Live:  {live_stats['total']} trades | WR={live_stats['win_rate']:.1%}")
        logger.info(f"   Clean days: {clean_days} | CB Active: {cb_active}")
        logger.info(f"{'─'*55}")

        decision = prev_mode
        reason   = "no_change"
        checks   = {}

        # ── إذا كنا في LIVE — فحص التراجع ──────────
        if prev_mode == "LIVE":
            if cb_active:
                decision = "PAPER"
                reason   = "circuit_breaker_triggered"
                logger.warning("  🚨 Circuit breaker active → تراجع فوري إلى PAPER")
            elif (live_stats["total"] >= PAPER_TRIGGERS["live_min_trades"] and
                  live_stats["win_rate"] < PAPER_TRIGGERS["live_win_rate_min"]):
                decision = "PAPER"
                reason   = f"live_win_rate_too_low ({live_stats['win_rate']:.1%})"
                logger.warning(f"  📉 Win rate LIVE منخفض جداً → تراجع إلى PAPER")
            else:
                logger.info("  ✅ LIVE mode: أداء مقبول — لا تغيير")
                decision = "LIVE"
                reason   = "live_performance_ok"

        # ── إذا كنا في PAPER — فحص شروط التحوّل ──
        elif prev_mode == "PAPER":
            req = LIVE_REQUIREMENTS
            checks = {
                "enough_trades":  paper_stats["total"]       >= req["min_paper_trades"],
                "win_rate_ok":    paper_stats["win_rate"]    >= req["min_win_rate"],
                "drawdown_ok":    paper_stats["max_drawdown"] < req["max_drawdown"] * 1000,  # بالدولار
                "clean_days_ok":  clean_days                 >= req["clean_days_required"],
                "regime_safe":    regime                      in req["allowed_regimes"],
                "cb_clear":       not cb_active,
            }

            all_pass = all(checks.values())
            checks_str = " | ".join([f"{'✅' if v else '❌'} {k}" for k, v in checks.items()])
            logger.info(f"  Checks: {checks_str}")

            if all_pass:
                decision = "LIVE"
                reason   = "all_conditions_met"
                logger.info("  🟢 جميع الشروط مستوفاة → تحوّل إلى LIVE")
            else:
                failed = [k for k, v in checks.items() if not v]
                reason = f"conditions_not_met: {failed}"
                logger.info(f"  🟡 PAPER: شروط ناقصة: {failed}")

        # ── حفظ وإعلان إذا تغيّر الوضع ─────────────
        if decision != prev_mode:
            self._current_mode = decision
            self._save_mode(decision, reason)
            logger.info(f"  🔁 تغيّر الوضع: {prev_mode} → {decision} ({reason})")
        else:
            self._save_mode(decision, reason)  # تحديث timestamp

        return {
            "mode":         decision,
            "prev_mode":    prev_mode,
            "changed":      decision != prev_mode,
            "reason":       reason,
            "checks":       checks,
            "paper_stats":  paper_stats,
            "live_stats":   live_stats,
            "clean_days":   clean_days,
            "regime":       regime,
        }

    @property
    def mode(self) -> str:
        return self._current_mode


_switcher_instance = None

def get_mode_switcher() -> LiveToPaperSwitcher:
    global _switcher_instance
    if _switcher_instance is None:
        _switcher_instance = LiveToPaperSwitcher()
    return _switcher_instance


if __name__ == "__main__":
    switcher = get_mode_switcher()
    result   = switcher.evaluate()
    print(json.dumps({
        "mode":      result["mode"],
        "changed":   result["changed"],
        "reason":    result["reason"],
        "checks":    result["checks"],
    }, ensure_ascii=False, indent=2))
