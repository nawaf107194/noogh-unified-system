#!/usr/bin/env python3
"""
NOOGH Trading Integration System — مسار A
------------------------------------------
يربط autonomous_trading_agent بدورة الـ Orchestrator الرئيسية.

المهام:
  1. يُشغّل وكيل التداول كـ subprocess أو استدعاء مباشر
  2. يُمرّر synthesis (القرار الاستراتيجي) كـ context للتداول
  3. يقرأ نتائج التداول من DB ويُعيدها للـ Orchestrator
  4. يُحدّث shared_memory.sqlite بحالة التداول الحالية
"""

import sys, os, json, time, sqlite3, logging, subprocess, re
from datetime import datetime
from typing import Dict, List, Any, Optional

sys.path.insert(0, "/home/noogh/projects/noogh_unified_system/src")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | trading_integration | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            "/home/noogh/projects/noogh_unified_system/src/logs/trading_integration.log"
        ),
    ]
)
logger = logging.getLogger("trading_integration")

SRC     = "/home/noogh/projects/noogh_unified_system/src"
DB_PATH = f"{SRC}/data/shared_memory.sqlite"
VENV_PY = f"{SRC}/.venv/bin/python3"


class TradingIntegrationSystem:
    """
    طبقة التكامل بين Orchestrator ووكيل التداول
    """

    def __init__(self):
        self._cycle_count = 0
        self._last_trading_status: Dict = {}
        self._last_run_time: float = 0.0
        # الحد الأدنى بين دورتي تداول: 4 دقائق (لا يشغّل كل دورة orchestrator)
        self._min_interval_sec = 240
        logger.info("📈 TradingIntegrationSystem initialized")
        logger.info(f"   Min interval between trading cycles: {self._min_interval_sec}s")

    # ─────────────────────────────────────────────
    # القراءة من shared_memory
    # ─────────────────────────────────────────────

    def _read_trading_state(self) -> Dict:
        """يقرأ آخر حالة تداول من shared_memory.sqlite"""
        state = {
            "open_positions": 0,
            "daily_pnl": 0.0,
            "paper_balance": 1000.0,
            "total_paper_trades": 0,
            "win_rate": 0.0,
            "circuit_breaker_active": False,
            "last_signal": None,
            "last_update": None,
        }
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()

            # حالة التداول الأخيرة من beliefs
            cur.execute(
                "SELECT value FROM beliefs WHERE key='trading:live_state' ORDER BY updated_at DESC LIMIT 1"
            )
            row = cur.fetchone()
            if row:
                stored = json.loads(row[0])
                state.update(stored)

            # إجمالي paper trades + win rate من جدول paper_trades
            try:
                cur.execute("SELECT COUNT(*), SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) FROM paper_trades")
                r = cur.fetchone()
                if r and r[0]:
                    total = r[0] or 0
                    wins  = r[1] or 0
                    state["total_paper_trades"] = total
                    state["win_rate"] = round((wins / total) * 100, 1) if total > 0 else 0.0
            except Exception:
                pass

            conn.close()
        except Exception as e:
            logger.warning(f"  ⚠️ Could not read trading state: {e}")
        return state

    # ─────────────────────────────────────────────
    # الكتابة إلى shared_memory
    # ─────────────────────────────────────────────

    def _write_trading_context(self, synthesis: Dict, orchestrator_cycle: int):
        """
        يكتب القرار الاستراتيجي (synthesis) في DB
        حتى يقرأه autonomous_trading_agent في دورته القادمة
        """
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()
            context = {
                "orchestrator_cycle": orchestrator_cycle,
                "key_decision":       synthesis.get("key_decision", ""),
                "next_hour_focus":    synthesis.get("next_hour_focus", ""),
                "is_evolving_correctly": synthesis.get("is_evolving_correctly", True),
                "overall_score":      synthesis.get("overall_score", 0.5),
                "self_insight":       synthesis.get("self_insight", ""),
                "timestamp":          datetime.now().isoformat(),
            }
            cur.execute(
                "INSERT OR REPLACE INTO beliefs (key, value, utility_score, updated_at) "
                "VALUES (?, ?, ?, ?)",
                ("trading:orchestrator_context",
                 json.dumps(context, ensure_ascii=False),
                 0.95, time.time())
            )
            conn.commit()
            conn.close()
            logger.info(f"  📝 Orchestrator context written to DB (cycle #{orchestrator_cycle})")
        except Exception as e:
            logger.error(f"  ❌ Failed to write trading context: {e}")

    # ─────────────────────────────────────────────
    # تشغيل وكيل التداول كـ subprocess
    # ─────────────────────────────────────────────

    def _launch_trading_cycle(self, timeout: int = 90) -> Dict:
        """
        يُطلق دورة تداول واحدة (--once) من autonomous_trading_agent
        ويلتقط نتيجتها
        """
        script = f"{SRC}/agents/autonomous_trading_agent.py"
        cmd = [VENV_PY, script, "--once"]
        try:
            env = os.environ.copy()
            env["PYTHONPATH"] = SRC
            r = subprocess.run(
                cmd,
                capture_output=True, text=True,
                timeout=timeout, cwd=SRC, env=env
            )
            success = r.returncode == 0
            stdout  = r.stdout[-3000:]
            stderr  = r.stderr[-500:]

            # استخراج إشارات من الـ stdout
            signals_found = len(re.findall(r'Paper Position|LIVE TRADE|EXECUTE', stdout))
            pnl_match     = re.search(r'P&L:\s*\$([\-\d\.]+)', stdout)
            pnl_value     = float(pnl_match.group(1)) if pnl_match else 0.0

            return {
                "success":       success,
                "signals_found": signals_found,
                "pnl_this_cycle": pnl_value,
                "stdout_preview": stdout[-800:],
                "exit_code":     r.returncode,
            }
        except subprocess.TimeoutExpired:
            logger.warning(f"  ⏱️ Trading agent timed out after {timeout}s")
            return {"success": False, "error": "timeout", "signals_found": 0, "pnl_this_cycle": 0.0}
        except Exception as e:
            logger.error(f"  ❌ Trading launch error: {e}")
            return {"success": False, "error": str(e), "signals_found": 0, "pnl_this_cycle": 0.0}

    # ─────────────────────────────────────────────
    # الواجهة الرئيسية (تُستدعى من Orchestrator)
    # ─────────────────────────────────────────────

    def run_with_context(self, synthesis: Dict, orchestrator_cycle: int) -> Dict:
        """
        يُشغّل دورة تداول مكتملة مع تمرير السياق الاستراتيجي

        يُعيد:
            dict يحتوي على:
              - trading_state: حالة التداول الحالية
              - cycle_result:  نتيجة الدورة
              - summary:       ملخص للـ Orchestrator
        """
        self._cycle_count += 1

        logger.info("\n" + "─" * 55)
        logger.info(f"📈 [TRADING INTEGRATION] دورة تداول #{self._cycle_count}")
        logger.info("─" * 55)

        # ── فحص الـ interval ──
        now = time.time()
        elapsed_since_last = now - self._last_run_time
        if self._last_run_time > 0 and elapsed_since_last < self._min_interval_sec:
            wait_left = self._min_interval_sec - elapsed_since_last
            logger.info(f"  ⏭️ Too soon ({elapsed_since_last:.0f}s since last run). Skipping (wait {wait_left:.0f}s more).")
            state = self._read_trading_state()
            return {
                "trading_state": state,
                "cycle_result":  {"skipped": True, "reason": "interval"},
                "summary":       self._build_summary(state, {}),
            }

        # ① تمرير السياق الاستراتيجي
        self._write_trading_context(synthesis, orchestrator_cycle)

        # ② تشغيل دورة التداول
        logger.info("  🚀 Launching autonomous_trading_agent --once ...")
        cycle_result = self._launch_trading_cycle(timeout=90)
        self._last_run_time = time.time()

        # ③ قراءة الحالة المحدّثة من DB
        state = self._read_trading_state()

        # ④ بناء الملخص
        summary = self._build_summary(state, cycle_result)

        # ⑤ نشر الملخص في DB للـ Synthesizer
        self._publish_trading_summary(summary)

        logger.info(f"  {'✅' if cycle_result.get('success') else '⚠️'} "
                    f"Signals: {cycle_result.get('signals_found', 0)} | "
                    f"Win Rate: {state.get('win_rate', 0)}% | "
                    f"PnL: ${state.get('daily_pnl', 0):.2f}")

        return {
            "trading_state": state,
            "cycle_result":  cycle_result,
            "summary":       summary,
        }

    def _build_summary(self, state: Dict, cycle_result: Dict) -> Dict:
        return {
            "open_positions":     state.get("open_positions", 0),
            "daily_pnl":          state.get("daily_pnl", 0.0),
            "paper_balance":      state.get("paper_balance", 1000.0),
            "total_trades":       state.get("total_paper_trades", 0),
            "win_rate":           state.get("win_rate", 0.0),
            "circuit_breaker":    state.get("circuit_breaker_active", False),
            "signals_this_cycle": cycle_result.get("signals_found", 0),
            "pnl_this_cycle":     cycle_result.get("pnl_this_cycle", 0.0),
            "timestamp":          datetime.now().isoformat(),
        }

    def _publish_trading_summary(self, summary: Dict):
        """ينشر ملخص التداول في shared_memory للـ KnowledgeSynthesizer"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO beliefs (key, value, utility_score, updated_at) "
                "VALUES (?, ?, ?, ?)",
                ("trading:latest_summary",
                 json.dumps(summary, ensure_ascii=False),
                 0.97, time.time())
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"  ❌ Failed to publish trading summary: {e}")


if __name__ == "__main__":
    # اختبار مباشر
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--test", action="store_true")
    args = p.parse_args()

    system = TradingIntegrationSystem()
    dummy_synthesis = {
        "key_decision": "مراقبة السوق وانتظار إشارة قوية",
        "next_hour_focus": "تحليل BTC وETH",
        "is_evolving_correctly": True,
        "overall_score": 0.8,
    }
    result = system.run_with_context(dummy_synthesis, orchestrator_cycle=1)
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
