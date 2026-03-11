#!/usr/bin/env python3
"""
NOOGH Adaptive Strategy Selector
----------------------------------
يُحلّل أداء كل استراتيجية في كل Vol Regime
ويكتب الأولويات في DB لـ autonomous_trading_agent.

يُستدعى من الـ Orchestrator كل دورتين.
"""

import sys, os, json, time, sqlite3, logging
from datetime import datetime
from typing import Dict, List

sys.path.insert(0, "/home/noogh/projects/noogh_unified_system/src")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | strategy_selector | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            "/home/noogh/projects/noogh_unified_system/src/logs/strategy_selector.log"
        ),
    ]
)
logger = logging.getLogger("strategy_selector")

SRC     = "/home/noogh/projects/noogh_unified_system/src"
DB_PATH = f"{SRC}/data/shared_memory.sqlite"

# الحد الأدنى للصفقات قبل الحكم على استراتيجية
MIN_TRADES_TO_JUDGE = 5
# Win Rate أدنى من هذا → معطّلة في هذا الـ Regime
DISABLE_THRESHOLD   = 0.40
# Win Rate أعلى من هذا → مُفضَّلة
PREFER_THRESHOLD    = 0.58


class AdaptiveStrategySelector:
    """
    يختار الاستراتيجيات المناسبة بناءً على:
      - الـ Vol Regime الحالي
      - أداء كل استراتيجية في هذا الـ Regime تاريخياً
    """

    def __init__(self):
        logger.info("🎯 AdaptiveStrategySelector initialized")

    # ─────────────────────────────────────────────
    # قراءة البيانات
    # ─────────────────────────────────────────────

    def _get_current_regime(self) -> str:
        """يقرأ الـ Vol Regime الحالي من DB"""
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
                data = json.loads(row[0])
                return data.get("regime", "NORMAL")
        except Exception:
            pass
        return "NORMAL"

    def _fetch_trades_by_regime(self, regime: str, limit: int = 200) -> List[Dict]:
        """يجلب الصفقات التي نُفِّذت في نفس الـ Regime"""
        trades = []
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur  = conn.cursor()
            try:
                cur.execute(
                    "SELECT strategy, pnl, confidence FROM paper_trades "
                    "WHERE vol_regime = ? ORDER BY created_at DESC LIMIT ?",
                    (regime, limit)
                )
                for r in cur.fetchall():
                    trades.append({"strategy": r[0], "pnl": r[1], "confidence": r[2]})
            except Exception:
                # fallback: جلب كل الصفقات بدون فلتر regime
                cur.execute(
                    "SELECT strategy, pnl FROM paper_trades "
                    "ORDER BY created_at DESC LIMIT ?", (limit,)
                )
                for r in cur.fetchall():
                    trades.append({"strategy": r[0], "pnl": r[1], "confidence": 0.5})
            conn.close()
        except Exception as e:
            logger.warning(f"  ⚠️ fetch_trades_by_regime: {e}")
        return trades

    # ─────────────────────────────────────────────
    # تحليل الأداء
    # ─────────────────────────────────────────────

    def _analyze_strategies(self, trades: List[Dict]) -> Dict[str, Dict]:
        """يحسب أداء كل استراتيجية"""
        perf: Dict[str, Dict] = {}
        for t in trades:
            s = t.get("strategy") or "unknown"
            if s not in perf:
                perf[s] = {"total": 0, "wins": 0, "pnl": 0.0}
            perf[s]["total"] += 1
            perf[s]["pnl"]   += t.get("pnl") or 0.0
            if (t.get("pnl") or 0) > 0:
                perf[s]["wins"] += 1

        for s, v in perf.items():
            v["win_rate"] = round(v["wins"] / v["total"], 3) if v["total"] else 0.0
            v["avg_pnl"]  = round(v["pnl"] / v["total"], 2)  if v["total"] else 0.0
        return perf

    # ─────────────────────────────────────────────
    # الواجهة الرئيسية
    # ─────────────────────────────────────────────

    def select_and_publish(self) -> Dict:
        """
        يُحدّد الاستراتيجيات المُفضَّلة والمُعطَّلة
        ويكتبها في DB.
        """
        regime = self._get_current_regime()
        logger.info(f"\n{'─'*55}")
        logger.info(f"🎯 [STRATEGY SELECTOR] Regime الحالي: {regime}")
        logger.info(f"{'─'*55}")

        trades = self._fetch_trades_by_regime(regime)
        perf   = self._analyze_strategies(trades)

        preferred = []
        disabled  = []
        neutral   = []

        for strategy, v in perf.items():
            if v["total"] < MIN_TRADES_TO_JUDGE:
                neutral.append(strategy)  # بيانات غير كافية
                continue
            if v["win_rate"] >= PREFER_THRESHOLD:
                preferred.append(strategy)
            elif v["win_rate"] <= DISABLE_THRESHOLD:
                disabled.append(strategy)
            else:
                neutral.append(strategy)

        # ترتيب المُفضَّلة حسب win_rate
        preferred.sort(key=lambda s: perf.get(s, {}).get("win_rate", 0), reverse=True)

        result = {
            "regime":           regime,
            "preferred":        preferred,
            "disabled":         disabled,
            "neutral":          neutral,
            "strategy_perf":    perf,
            "updated_at":       datetime.now().isoformat(),
            "trades_analyzed":  len(trades),
        }

        logger.info(f"  ✅ مُفضَّلة ({len(preferred)}): {preferred}")
        logger.info(f"  ❌ مُعطَّلة ({len(disabled)}): {disabled}")
        logger.info(f"  ➖ محايدة  ({len(neutral)}):  {neutral}")

        # كتابة في DB ليقرأها autonomous_trading_agent
        self._publish(result)
        return result

    def _publish(self, result: Dict):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur  = conn.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO beliefs (key, value, utility_score, updated_at) "
                "VALUES (?, ?, ?, ?)",
                ("trading:strategy_selection",
                 json.dumps(result, ensure_ascii=False),
                 0.95, time.time())
            )
            conn.commit()
            conn.close()
            logger.info("  💾 Strategy selection saved to DB")
        except Exception as e:
            logger.error(f"  ❌ publish error: {e}")

    def get_current_selection(self) -> Dict:
        """يقرأ آخر selection من DB"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur  = conn.cursor()
            cur.execute(
                "SELECT value FROM beliefs WHERE key='trading:strategy_selection' LIMIT 1"
            )
            row = cur.fetchone()
            conn.close()
            return json.loads(row[0]) if row else {}
        except Exception:
            return {}


_selector_instance = None

def get_strategy_selector() -> AdaptiveStrategySelector:
    global _selector_instance
    if _selector_instance is None:
        _selector_instance = AdaptiveStrategySelector()
    return _selector_instance


if __name__ == "__main__":
    sel = get_strategy_selector()
    result = sel.select_and_publish()
    print(json.dumps({
        "regime":    result["regime"],
        "preferred": result["preferred"],
        "disabled":  result["disabled"],
    }, ensure_ascii=False, indent=2))
