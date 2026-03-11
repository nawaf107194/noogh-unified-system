#!/usr/bin/env python3
"""
NOOGH Trading Performance Reporter
------------------------------------
يُنشئ تقرير أداء يومي/أسبوعي شامل من paper_trades وbeliefs
ويحفظه في DB تحت مفتاح trading:daily_report
"""

import sys, os, json, time, sqlite3, logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

sys.path.insert(0, "/home/noogh/projects/noogh_unified_system/src")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | perf_reporter | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            "/home/noogh/projects/noogh_unified_system/src/logs/trading_performance.log"
        ),
    ]
)
logger = logging.getLogger("perf_reporter")

SRC     = "/home/noogh/projects/noogh_unified_system/src"
DB_PATH = f"{SRC}/data/shared_memory.sqlite"


class TradingPerformanceReporter:
    """
    يُولّد تقرير أداء شامل يُغذّي KnowledgeSynthesizer والـ TradingMemoryBridge
    """

    def __init__(self):
        logger.info("📊 TradingPerformanceReporter initialized")

    # ─────────────────────────────────────────────
    # جلب البيانات
    # ─────────────────────────────────────────────

    def _fetch_trades(self, days: int = 1) -> List[Dict]:
        """يجلب صفقات الـ N أيام الأخيرة من paper_trades"""
        trades = []
        cutoff = time.time() - (days * 86400)
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()
            cur.execute(
                "SELECT symbol, strategy, direction, entry_price, exit_price, "
                "pnl, confidence, closed_at FROM paper_trades "
                "WHERE closed_at >= ? ORDER BY closed_at DESC",
                (cutoff,)
            )
            for row in cur.fetchall():
                trades.append({
                    "symbol":      row[0],
                    "strategy":    row[1],
                    "direction":   row[2],
                    "entry":       row[3],
                    "exit":        row[4],
                    "pnl":         row[5] or 0.0,
                    "confidence":  row[6] or 0.0,
                    "closed_at":   row[7],
                })
            conn.close()
        except Exception as e:
            logger.warning(f"  ⚠️ fetch_trades error: {e}")
        return trades

    def _fetch_yesterday_report(self) -> Dict:
        """يجلب تقرير أمس للمقارنة"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()
            cur.execute("SELECT value FROM beliefs WHERE key='trading:daily_report' LIMIT 1")
            row = cur.fetchone()
            conn.close()
            return json.loads(row[0]) if row else {}
        except Exception:
            return {}

    # ─────────────────────────────────────────────
    # تحليل الأداء
    # ─────────────────────────────────────────────

    def _analyze(self, trades: List[Dict]) -> Dict:
        """يحلّل قائمة الصفقات ويعيد إحصاءات شاملة"""
        if not trades:
            return {
                "total": 0, "wins": 0, "losses": 0, "win_rate": 0.0,
                "total_pnl": 0.0, "avg_pnl": 0.0, "max_win": 0.0, "max_loss": 0.0,
                "by_strategy": {}, "by_symbol": {}, "by_direction": {},
                "drawdown_max": 0.0, "profit_factor": 0.0,
            }

        wins   = [t for t in trades if t["pnl"] > 0]
        losses = [t for t in trades if t["pnl"] <= 0]
        total_pnl = sum(t["pnl"] for t in trades)

        # Profit Factor
        gross_profit = sum(t["pnl"] for t in wins) if wins else 0.0
        gross_loss   = abs(sum(t["pnl"] for t in losses)) if losses else 0.001
        profit_factor = round(gross_profit / gross_loss, 2)

        # Max Drawdown
        running = 0.0
        peak    = 0.0
        max_dd  = 0.0
        for t in sorted(trades, key=lambda x: x["closed_at"]):
            running += t["pnl"]
            if running > peak:
                peak = running
            dd = peak - running
            if dd > max_dd:
                max_dd = dd

        # By Strategy
        by_strategy: Dict[str, Dict] = {}
        for t in trades:
            s = t["strategy"] or "unknown"
            if s not in by_strategy:
                by_strategy[s] = {"total": 0, "wins": 0, "pnl": 0.0}
            by_strategy[s]["total"] += 1
            by_strategy[s]["pnl"]   += t["pnl"]
            if t["pnl"] > 0:
                by_strategy[s]["wins"] += 1
        for s in by_strategy:
            t_ = by_strategy[s]["total"]
            by_strategy[s]["win_rate"] = round(
                by_strategy[s]["wins"] / t_ * 100, 1) if t_ else 0.0
            by_strategy[s]["pnl"] = round(by_strategy[s]["pnl"], 2)

        # By Symbol
        by_symbol: Dict[str, Dict] = {}
        for t in trades:
            sym = t["symbol"] or "unknown"
            if sym not in by_symbol:
                by_symbol[sym] = {"total": 0, "wins": 0, "pnl": 0.0}
            by_symbol[sym]["total"] += 1
            by_symbol[sym]["pnl"]   += t["pnl"]
            if t["pnl"] > 0:
                by_symbol[sym]["wins"] += 1
        for sym in by_symbol:
            t_ = by_symbol[sym]["total"]
            by_symbol[sym]["win_rate"] = round(
                by_symbol[sym]["wins"] / t_ * 100, 1) if t_ else 0.0

        # By Direction
        by_dir: Dict[str, Dict] = {}
        for t in trades:
            d = t["direction"] or "unknown"
            if d not in by_dir:
                by_dir[d] = {"total": 0, "wins": 0}
            by_dir[d]["total"] += 1
            if t["pnl"] > 0:
                by_dir[d]["wins"] += 1
        for d in by_dir:
            t_ = by_dir[d]["total"]
            by_dir[d]["win_rate"] = round(
                by_dir[d]["wins"] / t_ * 100, 1) if t_ else 0.0

        # Best / Worst strategy
        sorted_strat = sorted(by_strategy.items(),
                               key=lambda x: x[1].get("win_rate", 0), reverse=True)
        best_strategy  = sorted_strat[0][0] if sorted_strat else "—"
        worst_strategy = sorted_strat[-1][0] if len(sorted_strat) > 1 else "—"

        return {
            "total":          len(trades),
            "wins":           len(wins),
            "losses":         len(losses),
            "win_rate":       round(len(wins) / len(trades) * 100, 1),
            "total_pnl":      round(total_pnl, 2),
            "avg_pnl":        round(total_pnl / len(trades), 2),
            "max_win":        round(max(t["pnl"] for t in trades), 2),
            "max_loss":       round(min(t["pnl"] for t in trades), 2),
            "profit_factor":  profit_factor,
            "drawdown_max":   round(max_dd, 2),
            "by_strategy":    by_strategy,
            "by_symbol":      by_symbol,
            "by_direction":   by_dir,
            "best_strategy":  best_strategy,
            "worst_strategy": worst_strategy,
        }

    # ─────────────────────────────────────────────
    # بناء التقرير
    # ─────────────────────────────────────────────

    def generate_report(self, days: int = 1) -> Dict:
        """يُولّد التقرير الكامل ويحفظه في DB"""
        logger.info(f"\n" + "─" * 55)
        logger.info(f"📊 [REPORTER] تقرير أداء آخر {days} يوم...")
        logger.info("─" * 55)

        trades    = self._fetch_trades(days=days)
        analysis  = self._analyze(trades)
        yesterday = self._fetch_yesterday_report()

        # دلتا مقارنةً بالأمس
        wr_delta  = round(analysis["win_rate"] - yesterday.get("win_rate", analysis["win_rate"]), 1)
        pnl_delta = round(analysis["total_pnl"] - yesterday.get("total_pnl", 0.0), 2)

        # Vol regime من DB
        vol_regime = "UNKNOWN"
        vol_switches = 0
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()
            cur.execute("SELECT value FROM beliefs WHERE key='volatility:regime_history' LIMIT 1")
            row = cur.fetchone()
            if row:
                hist = json.loads(row[0])
                if hist:
                    vol_regime   = hist[-1].get("regime", "UNKNOWN")
                    vol_switches = len(hist)
            conn.close()
        except Exception:
            pass

        # Circuit breaker count
        cb_count = 0
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()
            cur.execute("SELECT value FROM beliefs WHERE key='trading:blocked' LIMIT 1")
            row = cur.fetchone()
            if row:
                cb_count = json.loads(row[0]).get("count", 0)
            conn.close()
        except Exception:
            pass

        # أفضل درس من TradingMemoryBridge
        top_lesson = "لا دروس بعد"
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()
            cur.execute(
                "SELECT value FROM beliefs WHERE key LIKE 'trading:lesson:%' "
                "ORDER BY updated_at DESC LIMIT 1"
            )
            row = cur.fetchone()
            if row:
                top_lesson = json.loads(row[0]).get("lesson", top_lesson)
            conn.close()
        except Exception:
            pass

        report = {
            "date":           datetime.now().strftime("%Y-%m-%d"),
            "period_days":    days,
            "win_rate":       analysis["win_rate"],
            "win_rate_delta": wr_delta,
            "total_pnl":      analysis["total_pnl"],
            "pnl_delta":      pnl_delta,
            "total_trades":   analysis["total"],
            "profit_factor":  analysis["profit_factor"],
            "drawdown_max":   analysis["drawdown_max"],
            "best_strategy":  analysis["best_strategy"],
            "worst_strategy": analysis["worst_strategy"],
            "by_strategy":    analysis["by_strategy"],
            "by_symbol":      analysis["by_symbol"],
            "by_direction":   analysis["by_direction"],
            "vol_regime":     vol_regime,
            "vol_switches":   vol_switches,
            "circuit_breaks": cb_count,
            "top_lesson":     top_lesson,
            "generated_at":   datetime.now().isoformat(),
        }

        # ── طباعة التقرير ──
        self._print_report(report)

        # ── حفظ في DB ──
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO beliefs (key, value, utility_score, updated_at) "
                "VALUES (?, ?, ?, ?)",
                ("trading:daily_report",
                 json.dumps(report, ensure_ascii=False),
                 0.97, time.time())
            )
            conn.commit()
            conn.close()
            logger.info("  💾 Report saved to DB: trading:daily_report")
        except Exception as e:
            logger.error(f"  ❌ Failed to save report: {e}")

        return report

    def _print_report(self, r: Dict):
        wr_sign  = "+" if r["win_rate_delta"] >= 0 else ""
        pnl_sign = "+" if r["pnl_delta"] >= 0 else ""
        logger.info(f"\n" + "━" * 50)
        logger.info(f"  📊 NOOGH Trading Report — {r['date']}")
        logger.info("━" * 50)
        logger.info(f"  Win Rate:       {r['win_rate']}%  ({wr_sign}{r['win_rate_delta']}% vs prev)")
        logger.info(f"  PnL:            ${r['total_pnl']}  ({pnl_sign}${r['pnl_delta']})")
        logger.info(f"  Total Trades:   {r['total_trades']}")
        logger.info(f"  Profit Factor:  {r['profit_factor']}")
        logger.info(f"  Max Drawdown:   ${r['drawdown_max']}")
        logger.info(f"  Best Strategy:  {r['best_strategy']}")
        logger.info(f"  Worst Strategy: {r['worst_strategy']}")
        logger.info(f"  Vol Regime:     {r['vol_regime']} ({r['vol_switches']} switches)")
        logger.info(f"  Circuit Breaks: {r['circuit_breaks']}x")
        logger.info(f"  Top Lesson:     {r['top_lesson'][:60]}")
        logger.info("━" * 50)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=1)
    p.add_argument("--weekly", action="store_true")
    args = p.parse_args()
    days = 7 if args.weekly else args.days
    reporter = TradingPerformanceReporter()
    report = reporter.generate_report(days=days)
    print(json.dumps(report, ensure_ascii=False, indent=2))
