#!/usr/bin/env python3
"""
NOOGH Trading Memory Bridge — مسار C
---------------------------------------
يربط نتائج التداول بـ KnowledgeSynthesizer وجعل
الدورة الاستراتيجية تتضمن أداء التداول.

المهام:
  1. يقرأ نتائج التداول من paper_trades + beliefs
  2. يبني trading_context يُدمج في prompt الـ KnowledgeSynthesizer
  3. يكتب trading_lessons في beliefs لجعل الدورة تتعلم
  4. يتتبع أداء الاستراتيجيات عبر الزمن
  5. يُصدر تحذيرات إذا كان الأداء يتدهور
"""

import sys, os, json, time, sqlite3, logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, "/home/noogh/projects/noogh_unified_system/src")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | trading_memory | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            "/home/noogh/projects/noogh_unified_system/src/logs/trading_memory_bridge.log"
        ),
    ]
)
logger = logging.getLogger("trading_memory")

SRC     = "/home/noogh/projects/noogh_unified_system/src"
DB_PATH = f"{SRC}/data/shared_memory.sqlite"


class TradingMemoryBridge:
    """
    جسر التداول-الذاكرة — يجعل NOOGH يتعلم من الأداء المالي
    """

    def __init__(self):
        self._last_analysis_time: float = 0.0
        self._analysis_interval: float  = 300.0  # كل 5 دقائق
        logger.info("🔗 TradingMemoryBridge initialized")

    # ─────────────────────────────────────────
    # قراءة بيانات التداول
    # ─────────────────────────────────────────

    def _get_recent_trades(self, hours: int = 24) -> List[Dict]:
        """يجلب الصفقات المغلقة في آخر N ساعة"""
        trades = []
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur  = conn.cursor()
            since = time.time() - hours * 3600
            cur.execute("""
                SELECT symbol, side, entry_price, exit_price, pnl, pnl_pct,
                       brain_confidence, exit_reason, entry_time, exit_time
                FROM paper_trades
                WHERE exit_time IS NOT NULL
                  AND created_at >= ?
                ORDER BY created_at DESC
                LIMIT 100
            """, (since,))
            cols = [d[0] for d in cur.description]
            trades = [dict(zip(cols, row)) for row in cur.fetchall()]
            conn.close()
        except Exception as e:
            logger.warning(f"  Could not fetch trades: {e}")
        return trades

    def _get_trading_insights(self, limit: int = 10) -> List[str]:
        """يجلب آخر التعلمات المستخلصة من الصفقات"""
        insights = []
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur  = conn.cursor()
            cur.execute("""
                SELECT insight FROM trading_insights
                ORDER BY created_at DESC LIMIT ?
            """, (limit,))
            insights = [r[0] for r in cur.fetchall()]
            conn.close()
        except Exception as e:
            logger.warning(f"  Could not fetch insights: {e}")
        return insights

    def _get_trading_summary_from_beliefs(self) -> Dict:
        """يقرأ آخر ملخص تداول من beliefs"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur  = conn.cursor()
            cur.execute(
                "SELECT value FROM beliefs WHERE key='trading:latest_summary' LIMIT 1"
            )
            row = cur.fetchone()
            conn.close()
            if row:
                return json.loads(row[0])
        except Exception:
            pass
        return {}

    # ─────────────────────────────────────────
    # تحليل الأداء
    # ─────────────────────────────────────────

    def _compute_performance_metrics(self, trades: List[Dict]) -> Dict:
        """يحسب مقاييس الأداء من قائمة الصفقات"""
        if not trades:
            return {
                "total": 0, "wins": 0, "losses": 0,
                "win_rate": 0.0, "avg_pnl": 0.0,
                "total_pnl": 0.0, "best_trade": 0.0,
                "worst_trade": 0.0, "avg_confidence": 0.0,
                "stop_loss_rate": 0.0,
            }

        wins   = [t for t in trades if (t.get("pnl") or 0) > 0]
        losses = [t for t in trades if (t.get("pnl") or 0) <= 0]
        pnls   = [t.get("pnl") or 0.0 for t in trades]
        confs  = [t.get("brain_confidence") or 0 for t in trades]
        sl_hits = sum(1 for t in trades if t.get("exit_reason") == "STOP_LOSS")

        return {
            "total":          len(trades),
            "wins":           len(wins),
            "losses":         len(losses),
            "win_rate":       round(len(wins) / len(trades) * 100, 1),
            "avg_pnl":        round(sum(pnls) / len(pnls), 2),
            "total_pnl":      round(sum(pnls), 2),
            "best_trade":     round(max(pnls), 2),
            "worst_trade":    round(min(pnls), 2),
            "avg_confidence": round(sum(confs) / len(confs), 1) if confs else 0.0,
            "stop_loss_rate": round(sl_hits / len(trades) * 100, 1),
        }

    def _detect_performance_trend(self, trades: List[Dict]) -> Tuple[str, str]:
        """
        يكشف توجه الأداء: هل يتحسن أم يتدهور؟

        Returns:
            (trend: "improving" | "stable" | "degrading",
             description: str)
        """
        if len(trades) < 6:
            return "stable", "Insufficient data"

        mid    = len(trades) // 2
        recent = trades[:mid]   # الأحدث (DB مرتب تنازلياً)
        older  = trades[mid:]

        recent_wr = sum(1 for t in recent if (t.get("pnl") or 0) > 0) / len(recent) * 100
        older_wr  = sum(1 for t in older  if (t.get("pnl") or 0) > 0) / len(older)  * 100

        delta = recent_wr - older_wr

        if delta > 10:
            return "improving", f"Win rate ↑{delta:.1f}% ({older_wr:.0f}%→{recent_wr:.0f}%)"
        elif delta < -10:
            return "degrading", f"Win rate ↓{abs(delta):.1f}% ({older_wr:.0f}%→{recent_wr:.0f}%)"
        else:
            return "stable", f"Win rate stable (~{recent_wr:.0f}%)"

    # ─────────────────────────────────────────
    # بناء السياق للـ Synthesizer
    # ─────────────────────────────────────────

    def build_synthesis_context(self) -> str:
        """
        يبني نص السياق الذي يُدمج في prompt الـ KnowledgeSynthesizer
        ليجعل القرارات الاستراتيجية تعكس الأداء التداولي
        """
        trades    = self._get_recent_trades(hours=24)
        metrics   = self._compute_performance_metrics(trades)
        insights  = self._get_trading_insights(limit=5)
        summary   = self._get_trading_summary_from_beliefs()
        trend, trend_desc = self._detect_performance_trend(trades)

        lines = [
            "📊 أداء التداول (آخر 24 ساعة):",
            f"  الصفقات: {metrics['total']} | الرابح: {metrics['wins']} | الخاسر: {metrics['losses']}",
            f"  Win Rate: {metrics['win_rate']}% | إجمالي PnL: ${metrics['total_pnl']:.2f}",
            f"  أفضل صفقة: +${metrics['best_trade']:.2f} | أسوأ صفقة: ${metrics['worst_trade']:.2f}",
            f"  متوسط ثقة Brain: {metrics['avg_confidence']:.0f}%",
            f"  توجه الأداء: {trend.upper()} — {trend_desc}",
        ]

        if summary:
            lines += [
                f"  صفقات مفتوحة: {summary.get('open_positions', 0)}",
                f"  رصيد Paper: ${summary.get('paper_balance', 0):.2f}",
            ]

        if insights:
            lines.append("\n💡 أحدث دروس التداول:")
            for ins in insights[:3]:
                lines.append(f"  • {ins}")

        # تحذير عند التدهور
        if trend == "degrading":
            lines.append(
                "\n⚠️ تحذير: أداء التداول يتدهور — يجب مراجعة الاستراتيجية!"
            )

        return "\n".join(lines)

    # ─────────────────────────────────────────
    # استخلاص الدروس وحفظها
    # ─────────────────────────────────────────

    def extract_and_store_lessons(self, trades: List[Dict]) -> List[str]:
        """
        يستخلص دروساً من الصفقات الأخيرة ويحفظها في beliefs
        (بدون استدعاء LLM — قواعد محددة)
        """
        lessons = []

        # درس 1: High confidence ولكن SL
        high_conf_losses = [
            t for t in trades
            if (t.get("brain_confidence") or 0) >= 80
            and (t.get("pnl") or 0) < 0
        ]
        if len(high_conf_losses) >= 2:
            lessons.append(
                f"تنبيه: {len(high_conf_losses)} صفقة بثقة ≥80% خسرت — راجع فلاتر الدخول"
            )

        # درس 2: LONG أفضل من SHORT (أو العكس)
        longs  = [t for t in trades if t.get("side") == "LONG"]
        shorts = [t for t in trades if t.get("side") == "SHORT"]
        if len(longs) >= 3 and len(shorts) >= 3:
            long_wr  = sum(1 for t in longs  if (t.get("pnl") or 0) > 0) / len(longs)  * 100
            short_wr = sum(1 for t in shorts if (t.get("pnl") or 0) > 0) / len(shorts) * 100
            if abs(long_wr - short_wr) > 20:
                better = "LONG" if long_wr > short_wr else "SHORT"
                lessons.append(
                    f"{better} أفضل أداءً ({max(long_wr, short_wr):.0f}% مقابل {min(long_wr, short_wr):.0f}%) — ركّز عليها"
                )

        # درس 3: STOP_LOSS مرتفع جداً
        sl_rate = sum(1 for t in trades if t.get("exit_reason") == "STOP_LOSS")
        if trades and sl_rate / len(trades) > 0.6:
            lessons.append(
                f"معدل ضرب SL مرتفع ({sl_rate/len(trades)*100:.0f}%) — قد يكون SL ضيقاً جداً"
            )

        # حفظ الدروس في DB
        if lessons:
            try:
                conn = sqlite3.connect(DB_PATH, timeout=5)
                cur  = conn.cursor()
                for lesson in lessons:
                    cur.execute(
                        "INSERT OR REPLACE INTO beliefs (key, value, utility_score, updated_at) "
                        "VALUES (?, ?, ?, ?)",
                        (f"trading:lesson:{int(time.time())}",
                         json.dumps({"lesson": lesson, "timestamp": datetime.now().isoformat()},
                                    ensure_ascii=False),
                         0.92, time.time())
                    )
                conn.commit()
                conn.close()
                logger.info(f"  📚 {len(lessons)} trading lessons stored in memory")
            except Exception as e:
                logger.error(f"  ❌ Failed to store lessons: {e}")

        return lessons

    # ─────────────────────────────────────────
    # دورة كاملة (تُستدعى من Orchestrator)
    # ─────────────────────────────────────────

    def run_bridge_cycle(self) -> Dict:
        """
        دورة كاملة: اقرأ → حلّل → خزّن → أعد السياق

        Returns:
            dict يحتوي على:
              - metrics: أرقام الأداء
              - trend: توجه الأداء
              - lessons: الدروس المستخلصة
              - synthesis_context: النص الجاهز للـ Synthesizer
        """
        now = time.time()
        if now - self._last_analysis_time < self._analysis_interval:
            # إعادة آخر سياق بدون إعادة حساب
            cached_context = self.build_synthesis_context()
            return {"cached": True, "synthesis_context": cached_context}

        self._last_analysis_time = now

        logger.info("\n" + "─" * 55)
        logger.info("🔗 [TRADING MEMORY BRIDGE] تحليل أداء التداول...")
        logger.info("─" * 55)

        trades  = self._get_recent_trades(hours=24)
        metrics = self._compute_performance_metrics(trades)
        trend, trend_desc = self._detect_performance_trend(trades)
        lessons = self.extract_and_store_lessons(trades)
        context = self.build_synthesis_context()

        logger.info(
            f"  📊 Trades: {metrics['total']} | WR: {metrics['win_rate']}% | "
            f"PnL: ${metrics['total_pnl']:.2f} | Trend: {trend}"
        )

        if lessons:
            for lesson in lessons:
                logger.info(f"  📚 Lesson: {lesson}")

        # حفظ المقاييس في DB
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur  = conn.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO beliefs (key, value, utility_score, updated_at) "
                "VALUES (?, ?, ?, ?)",
                ("trading:performance_metrics",
                 json.dumps({**metrics, "trend": trend, "trend_desc": trend_desc,
                             "timestamp": datetime.now().isoformat()},
                            ensure_ascii=False),
                 0.94, time.time())
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"  ❌ Failed to save metrics: {e}")

        return {
            "cached":           False,
            "metrics":          metrics,
            "trend":            trend,
            "trend_desc":       trend_desc,
            "lessons":          lessons,
            "synthesis_context": context,
        }


if __name__ == "__main__":
    bridge = TradingMemoryBridge()
    result = bridge.run_bridge_cycle()
    print("\n📊 Trading Memory Bridge Output:")
    print(result["synthesis_context"])
    if result.get("lessons"):
        print("\n📚 Lessons:")
        for l in result["lessons"]:
            print(f"  • {l}")
