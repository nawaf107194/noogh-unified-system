#!/usr/bin/env python3
"""
NOOGH Live-to-Paper Switcher
-------------------------------
يحكم على متى يتحوّل NOOGH من paper trading إلى live
وعلى متى يتراجع من live إلى paper عند الخطر

يقرأ شروط الأمان ويكتب في DB:
  trading:mode = {"mode": "PAPER|LIVE", "reason": ..., "approved_at": ...}
"""

import sys, os, json, time, sqlite3, logging
from datetime import datetime, timedelta
from typing import Dict, Optional

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

# ── شروط الانتقال لـ LIVE ──
LIVE_REQUIREMENTS = {
    "min_paper_trades":      50,
    "min_win_rate":          60.0,   # %
    "max_drawdown":          3.0,    # $
    "cb_free_days":          7,      # أيام بدون circuit breaker
    "allowed_regimes":       ["CALM", "NORMAL"],
}

# ── شروط التراجع من LIVE إلى PAPER ──
REVERT_TRIGGERS = {
    "win_rate_below":        45.0,   # % على آخر 20 صفقة live
    "circuit_breaker":       True,   # أي CB يُفعَّل
    "max_live_drawdown":     5.0,    # $
    "consecutive_losses":    5,      # خسائر متتالية
}


class LiveToPaperSwitcher:
    """
    حارس وضع التداول — يُراقب ويُقرر
    """

    def __init__(self):
        self._current_mode = "PAPER"
        self._load_mode()
        logger.info(f"🔄 LiveToPaperSwitcher initialized | Mode: {self._current_mode}")

    def _load_mode(self):
        """يحمّل الوضع الحالي من DB"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()
            cur.execute("SELECT value FROM beliefs WHERE key='trading:mode' LIMIT 1")
            row = cur.fetchone()
            conn.close()
            if row:
                data = json.loads(row[0])
                self._current_mode = data.get("mode", "PAPER")
        except Exception:
            pass

    def _save_mode(self, mode: str, reason: str, extra: Dict = None):
        """يحفظ الوضع الجديد في DB"""
        data = {
            "mode":        mode,
            "reason":      reason,
            "changed_at":  datetime.now().isoformat(),
            "previous":    self._current_mode,
        }
        if extra:
            data.update(extra)
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO beliefs (key, value, utility_score, updated_at) "
                "VALUES (?, ?, ?, ?)",
                ("trading:mode", json.dumps(data, ensure_ascii=False), 0.99, time.time())
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"  ❌ save_mode error: {e}")
        self._current_mode = mode

    # ─────────────────────────────────────────────
    # قراءة مؤشرات الأداء
    # ─────────────────────────────────────────────

    def _get_paper_metrics(self) -> Dict:
        """يجمع مقاييس paper trading من DB"""
        metrics = {
            "total_trades": 0, "win_rate": 0.0,
            "max_drawdown": 0.0, "cb_free_days": 999,
            "current_regime": "NORMAL",
        }
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()

            # إجمالي الصفقات + WR
            cur.execute(
                "SELECT COUNT(*), "
                "SUM(CASE WHEN pnl > 0 THEN 1.0 ELSE 0.0 END) "
                "FROM paper_trades"
            )
            row = cur.fetchone()
            if row and row[0]:
                metrics["total_trades"] = row[0]
                metrics["win_rate"] = round((row[1] or 0) / row[0] * 100, 1)

            # Max Drawdown
            cur.execute(
                "SELECT pnl FROM paper_trades ORDER BY closed_at ASC"
            )
            pnls = [r[0] or 0.0 for r in cur.fetchall()]
            running, peak, max_dd = 0.0, 0.0, 0.0
            for p in pnls:
                running += p
                if running > peak:
                    peak = running
                dd = peak - running
                if dd > max_dd:
                    max_dd = dd
            metrics["max_drawdown"] = round(max_dd, 2)

            # آخر Circuit Breaker
            cur.execute(
                "SELECT value FROM beliefs WHERE key='trading:blocked' LIMIT 1"
            )
            row = cur.fetchone()
            if row:
                cb_data = json.loads(row[0])
                cb_time_str = cb_data.get("changed_at") or cb_data.get("timestamp")
                if cb_time_str:
                    cb_time = datetime.fromisoformat(cb_time_str)
                    days_since_cb = (datetime.now() - cb_time).days
                    metrics["cb_free_days"] = days_since_cb

            # الـ regime الحالي
            cur.execute(
                "SELECT value FROM beliefs WHERE key='volatility:current_regime' LIMIT 1"
            )
            row = cur.fetchone()
            if row:
                metrics["current_regime"] = json.loads(row[0]).get("regime", "NORMAL")

            conn.close()
        except Exception as e:
            logger.warning(f"  ⚠️ get_paper_metrics: {e}")
        return metrics

    def _get_live_metrics(self) -> Dict:
        """يجمع مقاييس live trading من DB"""
        metrics = {
            "recent_win_rate": 100.0,
            "circuit_breaker_active": False,
            "live_drawdown": 0.0,
            "consecutive_losses": 0,
        }
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()

            # WR آخر 20 صفقة live
            cur.execute(
                "SELECT pnl FROM live_trades ORDER BY closed_at DESC LIMIT 20"
            )
            rows = cur.fetchall()
            if rows:
                wins = sum(1 for r in rows if (r[0] or 0) > 0)
                metrics["recent_win_rate"] = round(wins / len(rows) * 100, 1)

            # Consecutive losses
            cur.execute(
                "SELECT pnl FROM live_trades ORDER BY closed_at DESC LIMIT 10"
            )
            rows = cur.fetchall()
            consec = 0
            for r in rows:
                if (r[0] or 0) <= 0:
                    consec += 1
                else:
                    break
            metrics["consecutive_losses"] = consec

            # Circuit Breaker state
            cur.execute(
                "SELECT value FROM beliefs WHERE key='volatility:circuit_breaker' LIMIT 1"
            )
            row = cur.fetchone()
            if row:
                cb = json.loads(row[0])
                metrics["circuit_breaker_active"] = cb.get("active", False)

            conn.close()
        except Exception as e:
            logger.warning(f"  ⚠️ get_live_metrics: {e}")
        return metrics

    # ─────────────────────────────────────────────
    # منطق القرار
    # ─────────────────────────────────────────────

    def _check_upgrade_to_live(self, metrics: Dict) -> Optional[str]:
        """
        يفحص إذا كانت شروط الانتقال لـ LIVE مكتملة
        يعيد None إذا مكتملة، أو سبب الرفض
        """
        r = LIVE_REQUIREMENTS
        checks = [
            (metrics["total_trades"] >= r["min_paper_trades"],
             f"Trades: {metrics['total_trades']}/{r['min_paper_trades']}"),
            (metrics["win_rate"] >= r["min_win_rate"],
             f"WinRate: {metrics['win_rate']}% < {r['min_win_rate']}%"),
            (metrics["max_drawdown"] <= r["max_drawdown"],
             f"Drawdown: ${metrics['max_drawdown']} > ${r['max_drawdown']}"),
            (metrics["cb_free_days"] >= r["cb_free_days"],
             f"CB-free days: {metrics['cb_free_days']}/{r['cb_free_days']}"),
            (metrics["current_regime"] in r["allowed_regimes"],
             f"Regime: {metrics['current_regime']} not in {r['allowed_regimes']}"),
        ]
        failures = [msg for passed, msg in checks if not passed]
        return failures[0] if failures else None

    def _check_revert_to_paper(self, metrics: Dict) -> Optional[str]:
        """
        يفحص إذا كان يجب التراجع لـ PAPER
        يعيد None إذا كل شيء جيد، أو سبب التراجع
        """
        t = REVERT_TRIGGERS
        if metrics.get("circuit_breaker_active"):
            return "Circuit Breaker مُفعَّل"
        if metrics.get("recent_win_rate", 100) < t["win_rate_below"]:
            return f"Win Rate انخفض لـ {metrics['recent_win_rate']}%"
        if metrics.get("live_drawdown", 0) >= t["max_live_drawdown"]:
            return f"Live Drawdown وصل ${metrics['live_drawdown']}"
        if metrics.get("consecutive_losses", 0) >= t["consecutive_losses"]:
            return f"{metrics['consecutive_losses']} خسائر متتالية"
        return None

    # ─────────────────────────────────────────────
    # الواجهة الرئيسية
    # ─────────────────────────────────────────────

    def evaluate(self) -> Dict:
        """
        يُقيّم الوضع الحالي ويُقرر التغيير إذا لزم
        يُعيد dict بالوضع الحالي وأسباب القرار
        """
        logger.info("\n" + "─" * 55)
        logger.info("🔄 [SWITCHER] تقييم وضع التداول...")
        logger.info("─" * 55)

        self._load_mode()
        result = {"mode": self._current_mode, "changed": False, "reason": "", "metrics": {}}

        if self._current_mode == "PAPER":
            metrics = self._get_paper_metrics()
            result["metrics"] = metrics
            failure_reason = self._check_upgrade_to_live(metrics)

            if failure_reason is None:
                # كل الشروط مكتملة — الانتقال لـ LIVE
                logger.info("  🚀 كل شروط LIVE مكتملة — الانتقال لـ LIVE TRADING")
                logger.info(f"     WR={metrics['win_rate']}% | DD=${metrics['max_drawdown']} | "
                            f"CB-free={metrics['cb_free_days']}d")
                self._save_mode("LIVE", "جميع شروط الأمان مكتملة", metrics)
                result.update({"mode": "LIVE", "changed": True,
                               "reason": "upgrade_to_live"})
            else:
                logger.info(f"  📋 تبقى PAPER | سبب: {failure_reason}")
                result["reason"] = failure_reason

        elif self._current_mode == "LIVE":
            metrics = self._get_live_metrics()
            result["metrics"] = metrics
            revert_reason = self._check_revert_to_paper(metrics)

            if revert_reason:
                logger.warning(f"  ⚠️ تراجع لـ PAPER | سبب: {revert_reason}")
                self._save_mode("PAPER", revert_reason, metrics)
                result.update({"mode": "PAPER", "changed": True,
                               "reason": f"revert: {revert_reason}"})
            else:
                logger.info(f"  ✅ LIVE مستمر | WR={metrics.get('recent_win_rate')}%")
                result["reason"] = "conditions_ok"

        # حفظ آخر تقييم في DB
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO beliefs (key, value, utility_score, updated_at) "
                "VALUES (?, ?, ?, ?)",
                ("trading:mode_evaluation",
                 json.dumps(result, ensure_ascii=False, default=str),
                 0.96, time.time())
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"  ❌ save evaluation: {e}")

        return result

    @property
    def current_mode(self) -> str:
        return self._current_mode


def get_mode_switcher() -> LiveToPaperSwitcher:
    """Singleton helper"""
    if not hasattr(get_mode_switcher, "_instance"):
        get_mode_switcher._instance = LiveToPaperSwitcher()
    return get_mode_switcher._instance


if __name__ == "__main__":
    switcher = LiveToPaperSwitcher()
    result = switcher.evaluate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
