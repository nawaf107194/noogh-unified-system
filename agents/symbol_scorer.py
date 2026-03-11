#!/usr/bin/env python3
"""
NOOGH Symbol Scorer
---------------------
يُحلّل كل رمز تداول بناءً على:
  1. Win Rate التاريخي في paper_trades
  2. Funding Rate (من funding_regime_detector)
  3. Volatility (ATR) المناسبة للـ regime الحالي
  4. عدد الصفقات (عينة كافية)

يكتب في DB:
  trading:top_symbols   = ["SOLUSDT", "BTCUSDT", ...]
  trading:avoid_symbols = ["XRPUSDT", ...]
"""

import sys, os, json, time, sqlite3, logging
from datetime import datetime
from typing import Dict, List, Tuple

sys.path.insert(0, "/home/noogh/projects/noogh_unified_system/src")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | symbol_scorer | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            "/home/noogh/projects/noogh_unified_system/src/logs/symbol_scorer.log"
        ),
    ]
)
logger = logging.getLogger("symbol_scorer")

SRC     = "/home/noogh/projects/noogh_unified_system/src"
DB_PATH = f"{SRC}/data/shared_memory.sqlite"

# ── وزن كل عامل في الـ Score النهائي ──
WEIGHT_WIN_RATE  = 0.50
WEIGHT_FUNDING   = 0.20
WEIGHT_VOLUME    = 0.15
WEIGHT_RECENCY   = 0.15

MIN_TRADES_FOR_SCORE = 5
TOP_N   = 5
AVOID_N = 3


class SymbolScorer:
    """
    يُصنّف رموز التداول بناءً على الأداء التاريخي + الظروف الحالية
    """

    def __init__(self):
        logger.info("🎯 SymbolScorer initialized")

    # ─────────────────────────────────────────────
    # جلب البيانات
    # ─────────────────────────────────────────────

    def _fetch_symbol_stats(self) -> Dict[str, Dict]:
        """يجمع إحصاءات كل رمز من paper_trades"""
        stats: Dict[str, Dict] = {}
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()
            cur.execute(
                "SELECT symbol, pnl, closed_at FROM paper_trades "
                "WHERE closed_at IS NOT NULL ORDER BY closed_at ASC"
            )
            for row in cur.fetchall():
                sym = row[0] or "unknown"
                pnl = row[1] or 0.0
                ts  = row[2] or 0.0
                if sym not in stats:
                    stats[sym] = {
                        "total": 0, "wins": 0, "pnl_sum": 0.0,
                        "first_ts": ts, "last_ts": ts
                    }
                stats[sym]["total"]   += 1
                stats[sym]["pnl_sum"] += pnl
                stats[sym]["last_ts"]  = ts
                if pnl > 0:
                    stats[sym]["wins"] += 1
            conn.close()
        except Exception as e:
            logger.warning(f"  ⚠️ fetch_symbol_stats: {e}")
        return stats

    def _fetch_funding_rates(self) -> Dict[str, float]:
        """
        يجلب funding rates من beliefs إذا موجودة
        (من funding_regime_detector.py أو funding_scanner_v2.py)
        """
        rates: Dict[str, float] = {}
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()
            # funding_scanner_v2 يكتب تحت مفاتيح متعددة
            cur.execute(
                "SELECT key, value FROM beliefs "
                "WHERE key LIKE 'funding:%' OR key LIKE 'market:funding%'"
            )
            for key, val in cur.fetchall():
                try:
                    data = json.loads(val)
                    if isinstance(data, dict):
                        for sym, rate in data.items():
                            if isinstance(rate, (int, float)):
                                rates[sym] = float(rate)
                except Exception:
                    pass
            conn.close()
        except Exception as e:
            logger.warning(f"  ⚠️ fetch_funding_rates: {e}")
        return rates

    def _get_current_regime(self) -> str:
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()
            cur.execute(
                "SELECT value FROM beliefs WHERE key='volatility:current_regime' LIMIT 1"
            )
            row = cur.fetchone()
            conn.close()
            if row:
                return json.loads(row[0]).get("regime", "NORMAL")
        except Exception:
            pass
        return "NORMAL"

    # ─────────────────────────────────────────────
    # حساب الـ Score
    # ─────────────────────────────────────────────

    def _score_symbol(self, sym: str, stat: Dict,
                       funding_rates: Dict[str, float],
                       regime: str,
                       now: float) -> float:
        """
        يحسب score مُركَّب لكل رمز [0.0 → 1.0]
        """
        if stat["total"] < MIN_TRADES_FOR_SCORE:
            return 0.0

        # 1. Win Rate Score
        win_rate = stat["wins"] / stat["total"]
        score_wr = win_rate  # 0 → 1

        # 2. Funding Rate Score
        # Funding إيجابي عالٍ = ضغط على LONG holders (سيء)
        # نريد funding قريب من الصفر أو سلبي قليلاً
        funding = funding_rates.get(sym, 0.0)
        if regime in ["CALM", "NORMAL"]:
            # نُفضَّل funding منخفض
            score_funding = max(0.0, 1.0 - abs(funding) * 1000)
        else:
            # في HIGH/EXTREME نُفضَّل funding سلبي (arb)
            score_funding = max(0.0, 1.0 - funding * 500) if funding < 0 else 0.5
        score_funding = min(1.0, max(0.0, score_funding))

        # 3. Volume Score — عدد الصفقات كمقياس للسيولة التاريخية
        score_volume = min(1.0, stat["total"] / 50.0)

        # 4. Recency Score — كم عدد الصفقات في آخر 7 أيام
        week_ago = now - 7 * 86400
        # نحتاج هذا من بيانات raw لكن نُقدّر من last_ts
        days_since_last = (now - stat["last_ts"]) / 86400
        score_recency = max(0.0, 1.0 - days_since_last / 14.0)  # يتلاشى خلال 14 يوم

        total_score = (
            score_wr      * WEIGHT_WIN_RATE +
            score_funding * WEIGHT_FUNDING  +
            score_volume  * WEIGHT_VOLUME   +
            score_recency * WEIGHT_RECENCY
        )
        return round(total_score, 3)

    # ─────────────────────────────────────────────
    # الواجهة الرئيسية
    # ─────────────────────────────────────────────

    def run(self) -> Dict:
        logger.info("\n" + "─" * 55)
        logger.info("🎯 [SYMBOL SCORER] تصنيف رموز التداول...")
        logger.info("─" * 55)

        stats         = self._fetch_symbol_stats()
        funding_rates = self._fetch_funding_rates()
        regime        = self._get_current_regime()
        now           = time.time()

        if not stats:
            logger.info("  ℹ️  لا بيانات صفقات بعد — سيتم التقييم لاحقاً")
            return {"top_symbols": [], "avoid_symbols": [], "scores": {}}

        # حساب الـ score لكل رمز
        scored: List[Tuple[str, float, Dict]] = []
        for sym, stat in stats.items():
            s = self._score_symbol(sym, stat, funding_rates, regime, now)
            win_rate = round(stat["wins"] / stat["total"] * 100, 1) if stat["total"] else 0.0
            scored.append((sym, s, {
                "score":      s,
                "win_rate":   win_rate,
                "total":      stat["total"],
                "pnl_sum":    round(stat["pnl_sum"], 2),
                "funding":    funding_rates.get(sym, 0.0),
            }))

        scored.sort(key=lambda x: x[1], reverse=True)

        top_symbols   = [x[0] for x in scored[:TOP_N] if x[1] > 0.4]
        avoid_symbols = [x[0] for x in scored[-AVOID_N:] if x[1] < 0.3 and
                         stats[x[0]]["total"] >= MIN_TRADES_FOR_SCORE]

        scores_dict = {x[0]: x[2] for x in scored}

        # لوج
        logger.info(f"  📊 Regime: {regime} | Symbols analyzed: {len(scored)}")
        for sym, score, detail in scored[:5]:
            logger.info(f"     {sym:12} score={score:.3f} | WR={detail['win_rate']}% | trades={detail['total']}")
        if avoid_symbols:
            logger.info(f"  ⚠️  Avoid: {avoid_symbols}")

        result = {
            "regime":        regime,
            "top_symbols":   top_symbols,
            "avoid_symbols": avoid_symbols,
            "scores":        scores_dict,
            "total_symbols": len(scored),
            "updated_at":    datetime.now().isoformat(),
        }

        # حفظ في DB
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO beliefs (key, value, utility_score, updated_at) "
                "VALUES (?, ?, ?, ?)",
                ("trading:top_symbols",
                 json.dumps(result, ensure_ascii=False),
                 0.94, time.time())
            )
            conn.commit()
            conn.close()
            logger.info(f"  💾 Saved → trading:top_symbols | Top: {top_symbols}")
        except Exception as e:
            logger.error(f"  ❌ save error: {e}")

        return result


def get_symbol_scorer() -> SymbolScorer:
    """Singleton helper"""
    if not hasattr(get_symbol_scorer, "_instance"):
        get_symbol_scorer._instance = SymbolScorer()
    return get_symbol_scorer._instance


if __name__ == "__main__":
    scorer = SymbolScorer()
    result = scorer.run()
    print(json.dumps(result, ensure_ascii=False, indent=2))
