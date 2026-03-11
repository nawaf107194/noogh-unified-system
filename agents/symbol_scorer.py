#!/usr/bin/env python3
"""
NOOGH Symbol Scorer
---------------------
يُحلّل كل رمز تداول ويُعطيه درجة بناءً على:
  1. Win Rate التاريخي في DB
  2. Funding Rate (من funding_regime_detector)
  3. Volatility النسبي (ATR%)
  4. السيولة (حجم التداول)

يكتب النتيجة في DB: {"top_symbols": [...], "avoid": [...]}
يُستدعى من الـ Orchestrator كل 6 دورات.
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

# الرموز الافتراضية
DEFAULT_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT",
    "XRPUSDT", "DOGEUSDT", "AVAXUSDT", "ADAUSDT",
]

# أوزان الدرجات (مجموعها = 1.0)
WEIGHTS = {
    "win_rate":   0.40,
    "funding":    0.25,   # funding rate منخفض = أفضل
    "volatility": 0.20,   # تقلّب معتدل = أفضل
    "pnl_total":  0.15,   # إجمالي الربح التاريخي
}


class SymbolScorer:
    """
    يُقيّم ويُرتّب رموز التداول.
    """

    def __init__(self):
        logger.info("🏆 SymbolScorer initialized")

    # ─────────────────────────────────────────────
    # جلب البيانات
    # ─────────────────────────────────────────────

    def _get_historical_perf(self) -> Dict[str, Dict]:
        """يجلب أداء كل رمز من paper_trades"""
        perf: Dict[str, Dict] = {}
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur  = conn.cursor()
            cur.execute(
                "SELECT symbol, pnl FROM paper_trades ORDER BY created_at DESC LIMIT 500"
            )
            for symbol, pnl in cur.fetchall():
                if not symbol: continue
                if symbol not in perf:
                    perf[symbol] = {"total": 0, "wins": 0, "pnl": 0.0}
                perf[symbol]["total"] += 1
                perf[symbol]["pnl"]   += pnl or 0.0
                if (pnl or 0) > 0:
                    perf[symbol]["wins"] += 1
            conn.close()
        except Exception as e:
            logger.warning(f"  ⚠️ historical_perf error: {e}")
        for sym, v in perf.items():
            v["win_rate"] = v["wins"] / v["total"] if v["total"] else 0.5
        return perf

    def _get_funding_data(self) -> Dict[str, float]:
        """يجلب Funding Rate من DB (من funding_regime_detector)"""
        funding: Dict[str, float] = {}
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur  = conn.cursor()
            cur.execute(
                "SELECT value FROM beliefs WHERE key='funding:latest_rates' LIMIT 1"
            )
            row = cur.fetchone()
            conn.close()
            if row:
                data = json.loads(row[0])
                if isinstance(data, dict):
                    funding = {k: abs(float(v)) for k, v in data.items()}
        except Exception as e:
            logger.warning(f"  ⚠️ funding_data error: {e}")
        return funding

    def _get_volatility_data(self) -> Dict[str, float]:
        """يجلب ATR% لكل رمز من DB إذا توفّر"""
        vol: Dict[str, float] = {}
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur  = conn.cursor()
            cur.execute(
                "SELECT value FROM beliefs WHERE key='market:atr_pct' LIMIT 1"
            )
            row = cur.fetchone()
            conn.close()
            if row:
                vol = json.loads(row[0])
        except Exception:
            pass
        return vol

    # ─────────────────────────────────────────────
    # حساب الدرجة
    # ─────────────────────────────────────────────

    def _score_symbol(self, symbol: str, hist: Dict, funding: Dict,
                      volatility: Dict) -> Tuple[float, Dict]:
        """
        يُعيد (الدرجة الكلية, تفاصيل الدرجات)
        """
        sym_hist = hist.get(symbol, {"win_rate": 0.5, "pnl": 0.0, "total": 0})

        # ── Win Rate Score (0–1) ──────────────────
        wr_score = min(sym_hist["win_rate"] / 0.80, 1.0)  # 80% = full score

        # ── Funding Score (0–1) ──────────────────
        # funding منخفض = أفضل (0.01% = جيد, 0.10% = سيء)
        fr = funding.get(symbol, 0.05)
        funding_score = max(0.0, 1.0 - (fr / 0.10))

        # ── Volatility Score (0–1) ───────────────
        # تقلّب معتدل (1–3%) أفضل, أعلى من 5% سيء
        atr_pct = volatility.get(symbol, 2.0)
        if 1.0 <= atr_pct <= 3.0:
            vol_score = 1.0
        elif atr_pct < 1.0:
            vol_score = atr_pct  # تقلّب منخفض جداً = سيولة ضعيفة
        else:
            vol_score = max(0.0, 1.0 - (atr_pct - 3.0) / 5.0)

        # ── PnL Score (0–1) ─────────────────────
        pnl = sym_hist.get("pnl", 0.0)
        pnl_score = min(max(pnl / 100.0, 0.0), 1.0)  # $100 = full score

        total_score = (
            WEIGHTS["win_rate"]   * wr_score +
            WEIGHTS["funding"]    * funding_score +
            WEIGHTS["volatility"] * vol_score +
            WEIGHTS["pnl_total"]  * pnl_score
        )

        details = {
            "total_score":    round(total_score, 3),
            "win_rate":       round(sym_hist["win_rate"], 3),
            "win_rate_score": round(wr_score, 3),
            "funding_rate":   round(fr, 5),
            "funding_score":  round(funding_score, 3),
            "atr_pct":        round(atr_pct, 2),
            "vol_score":      round(vol_score, 3),
            "pnl_total":      round(pnl, 2),
            "pnl_score":      round(pnl_score, 3),
            "trades":         sym_hist.get("total", 0),
        }
        return total_score, details

    # ─────────────────────────────────────────────
    # الواجهة الرئيسية
    # ─────────────────────────────────────────────

    def score_and_publish(self, symbols: List[str] = None) -> Dict:
        """
        يُقيّم الرموز ويكتب النتيجة في DB.
        """
        symbols = symbols or DEFAULT_SYMBOLS
        logger.info(f"\n{'─'*55}")
        logger.info(f"🏆 [SYMBOL SCORER] تقييم {len(symbols)} رمز...")
        logger.info(f"{'─'*55}")

        hist       = self._get_historical_perf()
        funding    = self._get_funding_data()
        volatility = self._get_volatility_data()

        scores: List[Tuple[str, float, Dict]] = []
        for sym in symbols:
            score, details = self._score_symbol(sym, hist, funding, volatility)
            scores.append((sym, score, details))
            logger.info(
                f"  {sym:<12} score={score:.3f} | "
                f"WR={details['win_rate']:.1%} | "
                f"FR={details['funding_rate']:.4%} | "
                f"ATR={details['atr_pct']:.1f}%"
            )

        # ترتيب حسب الدرجة
        scores.sort(key=lambda x: x[1], reverse=True)

        # أفضل 3 وأسوأ 2
        top_symbols  = [s[0] for s in scores[:3]]
        avoid_symbols = [s[0] for s in scores if s[1] < 0.30]

        result = {
            "top_symbols":   top_symbols,
            "avoid":         avoid_symbols,
            "all_scores":    {s[0]: s[2] for s in scores},
            "updated_at":    datetime.now().isoformat(),
            "symbols_count": len(symbols),
        }

        logger.info(f"  🥇 أفضل:   {top_symbols}")
        logger.info(f"  ⛔ تجنّب:  {avoid_symbols}")

        # حفظ في DB
        self._publish(result)
        return result

    def _publish(self, result: Dict):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur  = conn.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO beliefs (key, value, utility_score, updated_at) "
                "VALUES (?, ?, ?, ?)",
                ("trading:symbol_scores",
                 json.dumps(result, ensure_ascii=False),
                 0.93, time.time())
            )
            conn.commit()
            conn.close()
            logger.info("  💾 Symbol scores saved to DB")
        except Exception as e:
            logger.error(f"  ❌ publish error: {e}")

    def get_top_symbols(self) -> List[str]:
        """يقرأ آخر top_symbols من DB"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur  = conn.cursor()
            cur.execute(
                "SELECT value FROM beliefs WHERE key='trading:symbol_scores' LIMIT 1"
            )
            row = cur.fetchone()
            conn.close()
            return json.loads(row[0]).get("top_symbols", DEFAULT_SYMBOLS[:3]) if row else DEFAULT_SYMBOLS[:3]
        except Exception:
            return DEFAULT_SYMBOLS[:3]


_scorer_instance = None

def get_symbol_scorer() -> SymbolScorer:
    global _scorer_instance
    if _scorer_instance is None:
        _scorer_instance = SymbolScorer()
    return _scorer_instance


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--symbols", nargs="+", default=None)
    args = p.parse_args()
    result = get_symbol_scorer().score_and_publish(symbols=args.symbols)
    print(json.dumps({
        "top":   result["top_symbols"],
        "avoid": result["avoid"],
    }, ensure_ascii=False, indent=2))
