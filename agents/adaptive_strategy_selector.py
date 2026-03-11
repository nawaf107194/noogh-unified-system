#!/usr/bin/env python3
"""
NOOGH Adaptive Strategy Selector
----------------------------------
يُحلّل أداء كل استراتيجية في كل Vol Regime
ويكتب في DB قائمة الاستراتيجيات المُفضَّلة والمُعطَّلة
لتقرأها autonomous_trading_agent قبل كل دورة
"""

import sys, os, json, time, sqlite3, logging
from datetime import datetime
from typing import Dict, List, Tuple

sys.path.insert(0, "/home/noogh/projects/noogh_unified_system/src")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | adaptive_selector | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            "/home/noogh/projects/noogh_unified_system/src/logs/adaptive_selector.log"
        ),
    ]
)
logger = logging.getLogger("adaptive_selector")

SRC     = "/home/noogh/projects/noogh_unified_system/src"
DB_PATH = f"{SRC}/data/shared_memory.sqlite"

# حد Win Rate للاستراتيجية: أقل من هذا → مُعطَّلة في هذا الـ regime
DISABLE_THRESHOLD  = 40.0   # %
# حد للأفضلية: أعلى من هذا → مُفضَّلة
PREFER_THRESHOLD   = 58.0   # %
# حد الحد الأدنى من الصفقات للحكم
MIN_SAMPLE         = 5


class AdaptiveStrategySelector:
    """
    يُحلّل paper_trades مجمّعةً حسب (strategy × vol_regime)
    ويُصدر توصية يقرأها autonomous_trading_agent
    """

    def __init__(self):
        logger.info("🧠 AdaptiveStrategySelector initialized")

    # ─────────────────────────────────────────────
    # جلب البيانات
    # ─────────────────────────────────────────────

    def _fetch_trades_with_regime(self, limit: int = 500) -> List[Dict]:
        """يجلب أحدث N صفقة مع vol_regime إذا متاح"""
        trades = []
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()
            # نحاول جلب vol_regime من عمود meta أو context
            cur.execute(
                "SELECT symbol, strategy, pnl, confidence, "
                "COALESCE(vol_regime, 'UNKNOWN') as regime "
                "FROM paper_trades ORDER BY closed_at DESC LIMIT ?",
                (limit,)
            )
            for row in cur.fetchall():
                trades.append({
                    "symbol":    row[0],
                    "strategy":  row[1] or "unknown",
                    "pnl":       row[2] or 0.0,
                    "confidence": row[3] or 0.0,
                    "regime":    row[4] or "UNKNOWN",
                })
            conn.close()
        except Exception:
            # إذا لم يوجد عمود vol_regime، نجلب بدونه
            try:
                conn = sqlite3.connect(DB_PATH, timeout=5)
                cur = conn.cursor()
                cur.execute(
                    "SELECT symbol, strategy, pnl, confidence "
                    "FROM paper_trades ORDER BY closed_at DESC LIMIT ?",
                    (limit,)
                )
                for row in cur.fetchall():
                    trades.append({
                        "symbol":    row[0],
                        "strategy":  row[1] or "unknown",
                        "pnl":       row[2] or 0.0,
                        "confidence": row[3] or 0.0,
                        "regime":    "UNKNOWN",
                    })
                conn.close()
            except Exception as e:
                logger.warning(f"  ⚠️ fetch_trades error: {e}")
        return trades

    def _get_current_regime(self) -> str:
        """يجلب الـ Vol Regime الحالي من DB"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()
            cur.execute(
                "SELECT value FROM beliefs WHERE key='volatility:current_regime' LIMIT 1"
            )
            row = cur.fetchone()
            conn.close()
            if row:
                data = json.loads(row[0])
                return data.get("regime", "NORMAL")
        except Exception:
            pass
        return "NORMAL"

    # ─────────────────────────────────────────────
    # التحليل
    # ─────────────────────────────────────────────

    def _analyze_by_regime(self, trades: List[Dict]) -> Dict[str, Dict[str, Dict]]:
        """
        يُجمّع أداء كل استراتيجية في كل regime
        returns: {regime: {strategy: {total, wins, win_rate, avg_pnl}}}
        """
        matrix: Dict[str, Dict] = {}
        for t in trades:
            reg  = t["regime"]
            strat = t["strategy"]
            if reg not in matrix:
                matrix[reg] = {}
            if strat not in matrix[reg]:
                matrix[reg][strat] = {"total": 0, "wins": 0, "pnl_sum": 0.0}
            matrix[reg][strat]["total"]   += 1
            matrix[reg][strat]["pnl_sum"] += t["pnl"]
            if t["pnl"] > 0:
                matrix[reg][strat]["wins"] += 1

        # حساب win_rate و avg_pnl
        for reg in matrix:
            for strat in matrix[reg]:
                d = matrix[reg][strat]
                d["win_rate"] = round(d["wins"] / d["total"] * 100, 1) if d["total"] else 0.0
                d["avg_pnl"]  = round(d["pnl_sum"] / d["total"], 2) if d["total"] else 0.0

        return matrix

    def _build_recommendations(self, matrix: Dict, current_regime: str) -> Dict:
        """
        يبني قائمة الاستراتيجيات المُفضَّلة والمُعطَّلة للـ regime الحالي
        """
        preferred: List[str] = []
        disabled:  List[str] = []
        reasoning: Dict[str, str] = {}

        # نبحث في UNKNOWN + الـ regime الحالي
        regimes_to_check = [current_regime, "UNKNOWN"]
        strategy_scores: Dict[str, List[float]] = {}

        for reg in regimes_to_check:
            if reg not in matrix:
                continue
            for strat, data in matrix[reg].items():
                if data["total"] < MIN_SAMPLE:
                    continue
                if strat not in strategy_scores:
                    strategy_scores[strat] = []
                strategy_scores[strat].append(data["win_rate"])

        for strat, scores in strategy_scores.items():
            avg_wr = sum(scores) / len(scores)
            if avg_wr >= PREFER_THRESHOLD:
                preferred.append(strat)
                reasoning[strat] = f"WR={avg_wr:.1f}% ✅"
            elif avg_wr < DISABLE_THRESHOLD:
                disabled.append(strat)
                reasoning[strat] = f"WR={avg_wr:.1f}% ❌"

        # ترتيب preferred حسب الأفضل
        if current_regime in matrix:
            preferred.sort(
                key=lambda s: matrix[current_regime].get(s, {}).get("win_rate", 0),
                reverse=True
            )

        return {
            "regime":            current_regime,
            "preferred_strategies": preferred,
            "disabled_strategies":  disabled,
            "reasoning":         reasoning,
            "min_sample":        MIN_SAMPLE,
            "updated_at":        datetime.now().isoformat(),
        }

    # ─────────────────────────────────────────────
    # الواجهة الرئيسية
    # ─────────────────────────────────────────────

    def run(self) -> Dict:
        logger.info("\n" + "─" * 55)
        logger.info("🧠 [ADAPTIVE] تحليل أداء الاستراتيجيات...")
        logger.info("─" * 55)

        trades         = self._fetch_trades_with_regime(limit=500)
        current_regime = self._get_current_regime()
        matrix         = self._analyze_by_regime(trades)
        recommendations = self._build_recommendations(matrix, current_regime)

        # لوج
        logger.info(f"  📊 Regime: {current_regime} | Trades analyzed: {len(trades)}")
        if recommendations["preferred_strategies"]:
            logger.info(f"  ✅ Preferred: {recommendations['preferred_strategies']}")
        if recommendations["disabled_strategies"]:
            logger.info(f"  ❌ Disabled:  {recommendations['disabled_strategies']}")
        if not recommendations["preferred_strategies"] and not recommendations["disabled_strategies"]:
            logger.info("  ℹ️  بيانات غير كافية بعد — كل الاستراتيجيات مسموحة")

        # حفظ في DB
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO beliefs (key, value, utility_score, updated_at) "
                "VALUES (?, ?, ?, ?)",
                ("trading:strategy_recommendations",
                 json.dumps(recommendations, ensure_ascii=False),
                 0.95, time.time())
            )
            # حفظ المصفوفة الكاملة أيضاً
            cur.execute(
                "INSERT OR REPLACE INTO beliefs (key, value, utility_score, updated_at) "
                "VALUES (?, ?, ?, ?)",
                ("trading:strategy_matrix",
                 json.dumps(matrix, ensure_ascii=False),
                 0.90, time.time())
            )
            conn.commit()
            conn.close()
            logger.info("  💾 Recommendations saved → trading:strategy_recommendations")
        except Exception as e:
            logger.error(f"  ❌ Save error: {e}")

        return recommendations


def get_adaptive_selector() -> AdaptiveStrategySelector:
    """Singleton helper"""
    if not hasattr(get_adaptive_selector, "_instance"):
        get_adaptive_selector._instance = AdaptiveStrategySelector()
    return get_adaptive_selector._instance


if __name__ == "__main__":
    selector = AdaptiveStrategySelector()
    result = selector.run()
    print(json.dumps(result, ensure_ascii=False, indent=2))
