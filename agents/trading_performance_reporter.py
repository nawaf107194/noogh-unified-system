#!/usr/bin/env python3
"""
NOOGH Trading Performance Reporter
------------------------------------
يُنشئ تقرير أداء يومي/أسبوعي شامل ويحفظه في DB.

يُستدعى من الـ Orchestrator كل 24 دورة (≈ يومياً) أو عند الطلب.
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
            "/home/noogh/projects/noogh_unified_system/src/logs/perf_reporter.log"
        ),
    ]
)
logger = logging.getLogger("perf_reporter")

SRC     = "/home/noogh/projects/noogh_unified_system/src"
DB_PATH = f"{SRC}/data/shared_memory.sqlite"


class TradingPerformanceReporter:
    """
    يُنشئ تقارير أداء تداول شاملة ويُخزّنها في DB.
    """

    def __init__(self):
        logger.info("📊 TradingPerformanceReporter initialized")

    # ─────────────────────────────────────────────
    # قراءة بيانات الصفقات
    # ─────────────────────────────────────────────

    def _fetch_trades(self, since_hours: int = 24) -> List[Dict]:
        """يجلب الصفقات من آخر N ساعة"""
        trades = []
        since_ts = time.time() - (since_hours * 3600)
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur  = conn.cursor()
            # محاولة جدول paper_trades أولاً
            try:
                cur.execute(
                    "SELECT symbol, side, entry_price, exit_price, pnl, "
                    "strategy, confidence, created_at "
                    "FROM paper_trades WHERE created_at > ? ORDER BY created_at DESC",
                    (since_ts,)
                )
                rows = cur.fetchall()
                for r in rows:
                    trades.append({
                        "symbol":     r[0], "side":       r[1],
                        "entry":      r[2], "exit":        r[3],
                        "pnl":        r[4], "strategy":    r[5],
                        "confidence": r[6] or 0.5,
                        "timestamp":  r[7],
                    })
            except Exception:
                pass

            # fallback: beliefs table
            if not trades:
                cur.execute(
                    "SELECT value FROM beliefs WHERE key LIKE 'trading:trade:%' "
                    "AND updated_at > ? ORDER BY updated_at DESC LIMIT 200",
                    (since_ts,)
                )
                for row in cur.fetchall():
                    try:
                        t = json.loads(row[0])
                        if isinstance(t, dict):
                            trades.append(t)
                    except Exception:
                        pass
            conn.close()
        except Exception as e:
            logger.warning(f"  ⚠️ fetch_trades error: {e}")
        return trades

    def _fetch_prev_report(self) -> Dict:
        """يجلب تقرير أمس للمقارنة"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur  = conn.cursor()
            cur.execute(
                "SELECT value FROM beliefs WHERE key='trading:daily_report_prev' LIMIT 1"
            )
            row = cur.fetchone()
            conn.close()
            return json.loads(row[0]) if row else {}
        except Exception:
            return {}

    # ─────────────────────────────────────────────
    # حساب الإحصائيات
    # ─────────────────────────────────────────────

    def _compute_stats(self, trades: List[Dict]) -> Dict:
        if not trades:
            return {
                "total": 0, "wins": 0, "losses": 0, "win_rate": 0.0,
                "total_pnl": 0.0, "avg_win": 0.0, "avg_loss": 0.0,
                "best_trade": 0.0, "worst_trade": 0.0,
                "profit_factor": 0.0, "max_drawdown": 0.0,
                "by_strategy": {}, "by_symbol": {},
            }

        total   = len(trades)
        winners = [t for t in trades if (t.get("pnl") or 0) > 0]
        losers  = [t for t in trades if (t.get("pnl") or 0) <= 0]
        wins    = len(winners)
        losses  = len(losers)
        pnls    = [t.get("pnl") or 0.0 for t in trades]

        total_pnl = sum(pnls)
        avg_win   = sum(t["pnl"] for t in winners) / wins  if wins   else 0.0
        avg_loss  = sum(t["pnl"] for t in losers)  / losses if losses else 0.0
        best      = max(pnls)
        worst     = min(pnls)

        gross_profit = sum(p for p in pnls if p > 0)
        gross_loss   = abs(sum(p for p in pnls if p < 0))
        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss else 0.0

        # Max Drawdown
        equity = 0.0
        peak   = 0.0
        max_dd = 0.0
        for p in pnls:
            equity += p
            if equity > peak:
                peak = equity
            dd = peak - equity
            if dd > max_dd:
                max_dd = dd

        # أداء كل استراتيجية
        by_strategy: Dict[str, Dict] = {}
        for t in trades:
            s = t.get("strategy") or "unknown"
            if s not in by_strategy:
                by_strategy[s] = {"total": 0, "wins": 0, "pnl": 0.0}
            by_strategy[s]["total"] += 1
            by_strategy[s]["pnl"]   += t.get("pnl") or 0.0
            if (t.get("pnl") or 0) > 0:
                by_strategy[s]["wins"] += 1
        for s, v in by_strategy.items():
            v["win_rate"] = round(v["wins"] / v["total"] * 100, 1) if v["total"] else 0.0

        # أداء كل رمز
        by_symbol: Dict[str, Dict] = {}
        for t in trades:
            sym = t.get("symbol") or "unknown"
            if sym not in by_symbol:
                by_symbol[sym] = {"total": 0, "wins": 0, "pnl": 0.0}
            by_symbol[sym]["total"] += 1
            by_symbol[sym]["pnl"]   += t.get("pnl") or 0.0
            if (t.get("pnl") or 0) > 0:
                by_symbol[sym]["wins"] += 1
        for sym, v in by_symbol.items():
            v["win_rate"] = round(v["wins"] / v["total"] * 100, 1) if v["total"] else 0.0

        return {
            "total":         total,
            "wins":          wins,
            "losses":        losses,
            "win_rate":      round(wins / total * 100, 1),
            "total_pnl":     round(total_pnl, 2),
            "avg_win":       round(avg_win, 2),
            "avg_loss":      round(avg_loss, 2),
            "best_trade":    round(best, 2),
            "worst_trade":   round(worst, 2),
            "profit_factor": profit_factor,
            "max_drawdown":  round(max_dd, 2),
            "by_strategy":   by_strategy,
            "by_symbol":     by_symbol,
        }

    # ─────────────────────────────────────────────
    # جلب بيانات Vol Regime من DB
    # ─────────────────────────────────────────────

    def _fetch_vol_summary(self) -> Dict:
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur  = conn.cursor()
            cur.execute(
                "SELECT value FROM beliefs WHERE key='trading:volatility_state' "
                "ORDER BY updated_at DESC LIMIT 1"
            )
            row = conn.execute(
                "SELECT value FROM beliefs WHERE key='trading:blocked' "
                "ORDER BY updated_at DESC LIMIT 20"
            ).fetchall()
            conn.close()
            blocks = len(row) if row else 0
            return {"circuit_blocks_today": blocks}
        except Exception:
            return {"circuit_blocks_today": 0}

    # ─────────────────────────────────────────────
    # بناء التقرير
    # ─────────────────────────────────────────────

    def generate_report(self, since_hours: int = 24) -> Dict:
        """
        يُنشئ تقرير الأداء ويُخزّنه في DB.
        يُعيد dict التقرير.
        """
        logger.info(f"\n{'─'*55}")
        logger.info(f"📊 [REPORTER] توليد تقرير آخر {since_hours} ساعة...")
        logger.info(f"{'─'*55}")

        trades      = self._fetch_trades(since_hours)
        stats       = self._compute_stats(trades)
        vol_summary = self._fetch_vol_summary()
        prev        = self._fetch_prev_report()

        # المقارنة مع أمس
        wr_delta   = round(stats["win_rate"]   - prev.get("win_rate", stats["win_rate"]), 1)
        pnl_delta  = round(stats["total_pnl"]  - prev.get("total_pnl", 0.0), 2)

        # أفضل وأسوأ استراتيجية
        strats = stats["by_strategy"]
        best_strategy  = max(strats, key=lambda s: strats[s]["win_rate"], default="—")
        worst_strategy = min(strats, key=lambda s: strats[s]["win_rate"], default="—")

        # آخر درس
        last_lesson = ""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur  = conn.cursor()
            cur.execute(
                "SELECT value FROM beliefs WHERE key LIKE 'trading:lesson:%' "
                "ORDER BY updated_at DESC LIMIT 1"
            )
            row = cur.fetchone()
            if row:
                lesson_data = json.loads(row[0])
                last_lesson = lesson_data.get("lesson") or lesson_data.get("text", "")
            conn.close()
        except Exception:
            pass

        report = {
            "generated_at":     datetime.now().isoformat(),
            "period_hours":     since_hours,
            "win_rate":         stats["win_rate"],
            "win_rate_delta":   wr_delta,
            "total_pnl":        stats["total_pnl"],
            "pnl_delta":        pnl_delta,
            "total_trades":     stats["total"],
            "wins":             stats["wins"],
            "losses":           stats["losses"],
            "avg_win":          stats["avg_win"],
            "avg_loss":         stats["avg_loss"],
            "profit_factor":    stats["profit_factor"],
            "max_drawdown":     stats["max_drawdown"],
            "best_strategy":    best_strategy,
            "worst_strategy":   worst_strategy,
            "circuit_blocks":   vol_summary["circuit_blocks_today"],
            "last_lesson":      last_lesson,
            "by_strategy":      strats,
            "by_symbol":        stats["by_symbol"],
        }

        # طباعة التقرير في اللوج
        self._print_report(report)

        # حفظ في DB
        self._save_report(report)

        return report

    def _print_report(self, r: Dict):
        wr_sign  = f"+{r['win_rate_delta']}" if r['win_rate_delta'] >= 0 else str(r['win_rate_delta'])
        pnl_sign = f"+${r['pnl_delta']:.2f}" if r['pnl_delta'] >= 0 else f"-${abs(r['pnl_delta']):.2f}"
        logger.info("")
        logger.info(f"{'━'*48}")
        logger.info(f"📊 NOOGH Daily Trading Report — {datetime.now().strftime('%Y-%m-%d')}")
        logger.info(f"{'━'*48}")
        logger.info(f"   Win Rate:       {r['win_rate']}%   ({wr_sign}% vs prev)")
        logger.info(f"   PnL Today:      ${r['total_pnl']:.2f}   ({pnl_sign})")
        logger.info(f"   Trades:         {r['total_trades']}  ({r['wins']}W / {r['losses']}L)")
        logger.info(f"   Profit Factor:  {r['profit_factor']}")
        logger.info(f"   Max Drawdown:   ${r['max_drawdown']:.2f}")
        logger.info(f"   Best Strategy:  {r['best_strategy']}")
        logger.info(f"   Worst Strategy: {r['worst_strategy']}")
        logger.info(f"   Circuit Blocks: {r['circuit_blocks']}x")
        if r['last_lesson']:
            logger.info(f"   Top Lesson:     {r['last_lesson'][:60]}")
        logger.info(f"{'━'*48}")
        logger.info("")

    def _save_report(self, report: Dict):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur  = conn.cursor()
            # احفظ الحالي كـ prev قبل الكتابة
            cur.execute("SELECT value FROM beliefs WHERE key='trading:daily_report'")
            existing = cur.fetchone()
            if existing:
                cur.execute(
                    "INSERT OR REPLACE INTO beliefs (key, value, utility_score, updated_at) "
                    "VALUES (?, ?, ?, ?)",
                    ("trading:daily_report_prev", existing[0], 0.80, time.time())
                )
            # احفظ التقرير الجديد
            cur.execute(
                "INSERT OR REPLACE INTO beliefs (key, value, utility_score, updated_at) "
                "VALUES (?, ?, ?, ?)",
                ("trading:daily_report",
                 json.dumps(report, ensure_ascii=False),
                 0.97, time.time())
            )
            conn.commit()
            conn.close()
            logger.info("  ✅ Report saved to DB")
        except Exception as e:
            logger.error(f"  ❌ save_report error: {e}")


_reporter_instance: TradingPerformanceReporter = None

def get_reporter() -> TradingPerformanceReporter:
    global _reporter_instance
    if _reporter_instance is None:
        _reporter_instance = TradingPerformanceReporter()
    return _reporter_instance


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--hours", type=int, default=24)
    args = p.parse_args()
    report = get_reporter().generate_report(since_hours=args.hours)
    print(json.dumps(report, ensure_ascii=False, indent=2))
