#!/usr/bin/env python3
"""
NOOGH Master Orchestrator — المنسّق الرئيسي

يربط جميع الأنظمة بطبقة الفهم:

  🎬 autonomous_learner      → يتعلم → يُفهَم → يُحفظ
  🖥️  server_control         → يراقب → يُفهَم → يتصرف
  🔍 deep_scanner            → يمسح  → يُفهَم → يُخزَّن
  🧠 brain_comprehension     ← طبقة الفهم المركزية
  📈 trading_integration    → تداول بوعي + حماية + ذاكرة
  📊 performance_reporter   → تقرير يومي شامل
  🎯 strategy_selector      → أفضل استراتيجية لكل Regime
  🔄 mode_switcher           → Paper ⇄ Live بشروط صارمة
  🏆 symbol_scorer          → أفضل رموز للتداول

تسلسل الدورة:
  1. تعلم + فهم
  2. مراقبة + فهم
  3. جلب سياق التداول (Bridge)
  4. وكلاء Sovereign
  5. مسح / تقطير / تطور ذاتي (كل N دورة)
  6. Symbol Scorer       (كل 6 دورات)
  7. Strategy Selector   (كل 2 دورة)
  8. Synthesis
  9. Trading Cycle
  10. Mode Switcher      (كل دورة)
  11. Performance Report  (كل 24 دورة)
  12. تحديث الأهداف
  13. تنفيذ القرار
"""

import sys, os, json, time, subprocess, sqlite3, logging, re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

sys.path.insert(0, "/home/noogh/projects/noogh_unified_system/src")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | orchestrator | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            "/home/noogh/projects/noogh_unified_system/src/logs/orchestrator.log"
        ),
    ]
)
logger = logging.getLogger("orchestrator")

SRC     = "/home/noogh/projects/noogh_unified_system/src"
DB_PATH = f"{SRC}/data/shared_memory.sqlite"
VENV_PY = f"{SRC}/.venv/bin/python3"


# ══════════════════════════════════════════════════════════
# helpers
# ══════════════════════════════════════════════════════════

def _safe_import(module_path: str, class_or_fn: str):
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("_mod", module_path)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return getattr(mod, class_or_fn, None)
    except Exception as e:
        logger.warning(f"  ⚠️ import failed {module_path}: {e}")
        return None


def _run_agent_script(script: str, args: List[str] = None,
                      timeout: int = 120) -> Dict:
    cmd = [VENV_PY, f"{SRC}/{script}"] + (args or [])
    try:
        req_env = os.environ.copy()
        req_env["PYTHONPATH"] = SRC
        r = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout, cwd=SRC, env=req_env
        )
        stdout_txt = r.stdout[-3000:]
        if r.returncode != 0 and not stdout_txt.strip():
            stdout_txt = r.stderr[-3000:]
        return {
            "success": r.returncode == 0,
            "stdout": stdout_txt,
            "stderr": r.stderr[-500:],
            "exit_code": r.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"timeout {timeout}s", "stdout": ""}
    except Exception as e:
        return {"success": False, "error": str(e), "stdout": ""}


def _db_inject(key: str, data: Any, utility: float = 0.90):
    try:
        conn = sqlite3.connect(DB_PATH, timeout=8)
        cur  = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO beliefs (key,value,utility_score,updated_at) VALUES (?,?,?,?)",
            (key, json.dumps(data, ensure_ascii=False, default=str), utility, time.time())
        )
        conn.commit(); conn.close()
    except Exception as e:
        logger.error(f"  DB error: {e}")


def _ask_brain(prompt: str, max_tokens: int = 600) -> str:
    import urllib.request
    VLLM_URL = os.environ.get("NEURAL_ENGINE_URL", "http://localhost:11434")
    MODEL    = os.environ.get("VLLM_MODEL_NAME", "qwen2.5-coder:7b")
    payload  = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content":
             "أنت NOOGH. قرّر وتصرف. أجوبتك ستُنفَّذ فوراً. كن دقيقاً وعملياً."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.2,
        "stream": False,
    }
    try:
        body = json.dumps(payload).encode()
        req  = urllib.request.Request(
            f"{VLLM_URL}/v1/chat/completions", data=body,
            headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.warning(f"  LLM: {e}")
        return ""


# ══════════════════════════════════════════════════════════
# وحدات الأنظمة
# ══════════════════════════════════════════════════════════

class LearningSystem:
    def run_and_comprehend(self) -> Dict:
        logger.info("\n" + "─"*55)
        logger.info("🎬 [LEARNING] تعلم من 5 مصادر...")
        logger.info("─"*55)
        r = _run_agent_script("agents/autonomous_learner_agent.py", ["--once"], timeout=120)
        tags_seen = set()
        for line in r["stdout"].split("\n"):
            if "Tags:" in line:
                tags = re.findall(r'[🎬🐙📜🟧📡]\s*\w[\w\s/]+', line)
                tags_seen.update(tags)
        cycle_summary = {
            "timestamp": datetime.now().isoformat(),
            "success": r["success"],
            "tags_learned": list(tags_seen)[:10],
            "output_preview": r["stdout"][-500:],
        }
        if r["success"] and tags_seen:
            logger.info(f"  🧠 فهم {len(tags_seen)} tags...")
            prompt = f"""أنت NOOGH تعلمت من YouTube/GitHub/arXiv/SO.
تعلمت: {list(tags_seen)[:8]}
Output: {r['stdout'][-800:]}
أجب JSON: {{"what_i_learned":"","most_valuable":"","how_to_apply":"","next_topic":"","learning_score":0.0}}"""
            response = _ask_brain(prompt)
            understanding = {}
            try:
                m = re.search(r'\{[\s\S]+\}', response)
                if m: understanding = json.loads(m.group())
            except Exception:
                understanding = {"raw": response[:200]}
            logger.info(f"  💎 {understanding.get('most_valuable','?')[:70]}")
            cycle_summary["understanding"] = understanding
            _db_inject("orchestrator:learning_cycle", cycle_summary, 0.93)
        else:
            logger.info("  ℹ️ لا تعلم جديد")
            _db_inject("orchestrator:learning_cycle", cycle_summary, 0.70)
        return cycle_summary


class MonitoringSystem:
    def _get_system_snapshot(self) -> Dict:
        snap = {}
        r = subprocess.run(
            "systemctl show noogh-agent noogh-neural noogh-gateway "
            "--property=ActiveState,MainPID,MemoryCurrent",
            shell=True, capture_output=True, text=True, timeout=5
        )
        services_raw = r.stdout
        snap["services_active"] = services_raw.count("ActiveState=active")
        snap["services_raw"]    = services_raw[:400]
        with open("/proc/meminfo") as f: mem = f.read()
        total = int(re.search(r"MemTotal:\s+(\d+)", mem).group(1))
        avail = int(re.search(r"MemAvailable:\s+(\d+)", mem).group(1))
        snap["ram_pct"]     = round((total - avail) / total * 100, 1)
        snap["ram_used_gb"] = round((total - avail) / 1024 / 1024, 1)
        with open("/proc/loadavg") as f: load = f.read().split()
        snap["load_1m"] = float(load[0])
        errors = []
        for log_file in ["agent_daemon_live.log", "autonomous_learner.log"]:
            try:
                path = Path(f"{SRC}/logs/{log_file}")
                if path.exists():
                    lines = path.read_text(errors="ignore").split("\n")
                    errors += [l for l in lines[-50:] if "ERROR" in l][-2:]
            except Exception: pass
        snap["recent_errors"] = errors[:4]
        snap["error_count"]   = len(errors)
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur  = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM beliefs")
            snap["beliefs_count"] = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM observations")
            snap["obs_count"] = cur.fetchone()[0]
            conn.close()
        except Exception: pass
        return snap

    def run_and_comprehend(self) -> Dict:
        logger.info("\n" + "─"*55)
        logger.info("🖥️  [MONITORING] مراقبة + فهم حالة النظام...")
        logger.info("─"*55)
        snap = self._get_system_snapshot()
        logger.info(
            f"  📊 {snap['services_active']}/3 | "
            f"RAM: {snap['ram_used_gb']}GB ({snap['ram_pct']}%) | Load: {snap['load_1m']}"
        )
        prompt = f"""أنت NOOGH تراقب نفسك.
خدمات ({snap['services_active']}/3): {snap['services_raw'][:200]}
RAM: {snap['ram_pct']}% | Load: {snap['load_1m']}
أخطاء: {snap['error_count']} | {chr(10).join(snap['recent_errors'][:2]) or 'لا أخطاء'}
أجب JSON: {{"status":"healthy|warning|critical","status_score":0.0,"biggest_concern":"","action_needed":true,"action":"","prediction":""}}"""
        response = _ask_brain(prompt)
        understanding = {}
        try:
            m = re.search(r'\{[\s\S]+\}', response)
            if m: understanding = json.loads(m.group())
        except Exception:
            understanding = {"raw": response[:200]}
        logger.info(f"  🩺 {understanding.get('status','?')} | 🔮 {understanding.get('prediction','?')[:50]}")
        result = {"snapshot": snap, "understanding": understanding}
        _db_inject("orchestrator:system_monitoring", result, 0.95)
        if understanding.get("status") == "critical":
            logger.warning("  🚨 حالة حرجة — تعافٍ ذاتي...")
            if snap["services_active"] < 3:
                subprocess.run(
                    "echo '107194' | sudo -S systemctl restart noogh-agent",
                    shell=True, capture_output=True, timeout=30
                )
        return result


class KnowledgeSynthesizer:
    def synthesize(self, learning_result: Dict, monitoring_result: Dict,
                   trading_context: str = "") -> Dict:
        logger.info("\n" + "─"*55)
        logger.info("🔮 [SYNTHESIS] تركيب المعرفة وتوجيه المسار...")
        logger.info("─"*55)
        l_u = learning_result.get("understanding", {})
        m_u = monitoring_result.get("understanding", {})
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur  = conn.cursor()
            cur.execute("SELECT value FROM beliefs WHERE key='system:strategic_goals'")
            row  = cur.fetchone()
            goals_str = row[0] if row else "{}"
            cur.execute(
                "SELECT key, utility_score FROM beliefs "
                "WHERE key != 'system:strategic_goals' "
                "ORDER BY utility_score DESC LIMIT 8"
            )
            top_beliefs = [{"key": r[0][:40], "u": round(r[1], 2)} for r in cur.fetchall()]
            conn.close()
        except Exception as e:
            logger.error(f"  DB error: {e}")
            top_beliefs = []; goals_str = "{}"
        trading_section = f"\n📈 سياق التداول:\n{trading_context[:400]}" if trading_context else ""
        prompt = f"""أنت NOOGH — تقرير الدورة وقرار المسار.
أهدافك: {goals_str}
أهم ما تعلمته: {l_u.get('most_valuable','لا شيء')}
حالة النظام: {m_u.get('status','?')} | {m_u.get('biggest_concern','none')}{trading_section}
أهم ما أؤمن: {[f"{b['key']}(u={b['u']})" for b in top_beliefs[:5]]}
أجب JSON: {{"key_decision":"","next_hour_focus":"","is_evolving_correctly":true,"self_insight":"","overall_score":0.0}}"""
        response = _ask_brain(prompt, max_tokens=500)
        synthesis = {}
        try:
            m = re.search(r'\{[\s\S]+\}', response)
            if m: synthesis = json.loads(m.group())
        except Exception:
            synthesis = {"raw": response[:200]}
        logger.info(f"  🎯 {synthesis.get('key_decision','?')[:65]}")
        logger.info(f"  ⏰ {synthesis.get('next_hour_focus','?')[:65]}")
        logger.info(f"  💭 {synthesis.get('self_insight','?')[:65]}")
        _db_inject("orchestrator:synthesis", synthesis, 0.98)
        return synthesis


class TradingSystem:
    """TradingIntegrationSystem + VolatilityGuard + TradingMemoryBridge"""

    def __init__(self):
        self._trading = self._bridge = self._guard = None
        self._available = False
        self._init_components()

    def _init_components(self):
        try:
            from agents.trading_integration_system import TradingIntegrationSystem
            from agents.trading_memory_bridge      import TradingMemoryBridge
            from agents.volatility_guard           import get_volatility_guard
            self._trading   = TradingIntegrationSystem()
            self._bridge    = TradingMemoryBridge()
            self._guard     = get_volatility_guard()
            self._available = True
            logger.info("  ✅ TradingSystem ready")
        except Exception as e:
            logger.warning(f"  ⚠️ TradingSystem init: {e}")

    def get_trading_context(self) -> str:
        if not self._available or not self._bridge: return ""
        try:
            return self._bridge.run_bridge_cycle().get("synthesis_context", "")
        except Exception as e:
            logger.warning(f"  ⚠️ bridge context: {e}")
            return ""

    def run_trading_cycle(self, synthesis: Dict, cycle_num: int,
                          mode: str = "PAPER") -> Dict:
        if not self._available:
            return {"skipped": True, "reason": "components not loaded"}
        logger.info("\n" + "─"*55)
        logger.info(f"📈 [TRADING] دورة تداول | Mode: {mode}")
        logger.info("─"*55)
        result = {}
        try:
            guard_result = self._guard.check_trading_allowed({})
            regime   = guard_result.get("regime", "UNKNOWN")
            allowed  = guard_result.get("allowed", True)
            vol_fac  = guard_result.get("volume_factor", 1.0)
            logger.info(f"  🛡️  {regime} | {'\u2705' if allowed else '\u274c'} | حجم: {vol_fac:.0%}")
            result["volatility"] = guard_result
            if not allowed:
                reason = guard_result.get("reason", "unknown")
                logger.warning(f"  🚫 موقوف: {reason}")
                _db_inject("trading:blocked", {"reason": reason, "regime": regime,
                           "timestamp": datetime.now().isoformat()}, 0.85)
                return {"blocked": True, "volatility": guard_result}
        except Exception as e:
            logger.warning(f"  ⚠️ VolatilityGuard: {e}")
            result["volatility"] = {"error": str(e)}
        try:
            trading_result = self._trading.run_with_context(synthesis, orchestrator_cycle=cycle_num)
            result["trading"] = trading_result
            logger.info(f"  🤖 {trading_result.get('status', 'done')}")
        except Exception as e:
            logger.warning(f"  ⚠️ TradingIntegration: {e}")
            result["trading"] = {"error": str(e)}
        try:
            bridge_result = self._bridge.run_bridge_cycle()
            logger.info(f"  🧠 Bridge: {bridge_result.get('performance_trend','stable')} | دروس: {bridge_result.get('lessons_stored',0)}")
            result["memory_bridge"] = bridge_result
        except Exception as e:
            logger.warning(f"  ⚠️ Bridge: {e}")
            result["memory_bridge"] = {"error": str(e)}
        _db_inject("trading:last_cycle", {
            "cycle": cycle_num, "timestamp": datetime.now().isoformat(), "result": result
        }, 0.90)
        return result


class TradingIntelligence:
    """
    يضمّ الأدوات الأربعة الجديدة:
      - TradingPerformanceReporter  (تقرير يومي)
      - AdaptiveStrategySelector   (أفضل استراتيجية لكل Regime)
      - LiveToPaperSwitcher        (مفتاح Paper/Live)
      - SymbolScorer               (ترتيب الرموز)
    """

    def __init__(self):
        self._reporter = None
        self._selector = None
        self._switcher = None
        self._scorer   = None
        self._available = False
        self._init()

    def _init(self):
        loaded = 0
        try:
            from agents.trading_performance_reporter import get_reporter
            self._reporter = get_reporter()
            loaded += 1
        except Exception as e:
            logger.warning(f"  ⚠️ PerformanceReporter: {e}")
        try:
            from agents.adaptive_strategy_selector import get_strategy_selector
            self._selector = get_strategy_selector()
            loaded += 1
        except Exception as e:
            logger.warning(f"  ⚠️ StrategySelector: {e}")
        try:
            from agents.live_to_paper_switcher import get_mode_switcher
            self._switcher = get_mode_switcher()
            loaded += 1
        except Exception as e:
            logger.warning(f"  ⚠️ ModeSwitcher: {e}")
        try:
            from agents.symbol_scorer import get_symbol_scorer
            self._scorer = get_symbol_scorer()
            loaded += 1
        except Exception as e:
            logger.warning(f"  ⚠️ SymbolScorer: {e}")
        self._available = loaded > 0
        logger.info(f"  📊 TradingIntelligence: {loaded}/4 محمَّل")

    # ── Symbol Scorer (كل 6 دورات) ───────────────────────
    def run_symbol_scoring(self) -> Dict:
        if not self._scorer:
            return {"skipped": True}
        try:
            result = self._scorer.score_and_publish()
            logger.info(
                f"  🏆 Top Symbols: {result.get('top_symbols',[])[:3]} | "
                f"Avoid: {result.get('avoid',[])}")
            return result
        except Exception as e:
            logger.warning(f"  ⚠️ SymbolScorer: {e}")
            return {"error": str(e)}

    # ── Strategy Selector (كل 2 دورتين) ───────────────────
    def run_strategy_selection(self) -> Dict:
        if not self._selector:
            return {"skipped": True}
        try:
            result = self._selector.select_and_publish()
            logger.info(
                f"  🎯 Regime: {result.get('regime')} | "
                f"Preferred: {result.get('preferred',[])} | "
                f"Disabled: {result.get('disabled',[])}")
            return result
        except Exception as e:
            logger.warning(f"  ⚠️ StrategySelector: {e}")
            return {"error": str(e)}

    # ── Mode Switcher (كل دورة) ───────────────────────────
    def run_mode_evaluation(self) -> str:
        if not self._switcher:
            return "PAPER"
        try:
            result = self._switcher.evaluate()
            mode    = result.get("mode", "PAPER")
            changed = result.get("changed", False)
            reason  = result.get("reason", "")
            if changed:
                logger.info(
                    f"  🔁 وضع التداول تغيّر: {result.get('prev_mode')} → {mode} ({reason})"
                )
            else:
                logger.info(f"  🔄 Mode: {mode} ({reason[:50]})")
            return mode
        except Exception as e:
            logger.warning(f"  ⚠️ ModeSwitcher: {e}")
            return "PAPER"

    # ── Performance Report (كل 24 دورة) ─────────────────
    def run_daily_report(self) -> Dict:
        if not self._reporter:
            return {"skipped": True}
        try:
            report = self._reporter.generate_report(since_hours=24)
            logger.info(
                f"  📊 تقرير يومي: WR={report.get('win_rate',0)}% | "
                f"PnL=${report.get('total_pnl',0):.2f} | "
                f"Trades={report.get('total_trades',0)}"
            )
            return report
        except Exception as e:
            logger.warning(f"  ⚠️ PerformanceReporter: {e}")
            return {"error": str(e)}


# ══════════════════════════════════════════════════════════
# المنسّق الرئيسي
# ══════════════════════════════════════════════════════════

class NooghOrchestrator:

    def __init__(self):
        self.learner     = LearningSystem()
        self.monitor     = MonitoringSystem()
        self.synthesizer = KnowledgeSynthesizer()
        self.trading     = TradingSystem()
        self.intelligence = TradingIntelligence()   # ← الأدوات الأربعة الجديدة

        try:
            from agents.decision_engine import DecisionEngine
            self.decision_engine = DecisionEngine()
        except ImportError:
            self.decision_engine = None
            logger.warning("  ⚠️ DecisionEngine not found")

        try:
            from agents.strategic_goals import StrategicGoalsSupervisor
            self.strategy = StrategicGoalsSupervisor()
        except ImportError:
            self.strategy = None
            logger.warning("  ⚠️ StrategicGoalsSupervisor not found")

        self._cycle = 0
        logger.info("🤖 NOOGH Orchestrator initialized")
        logger.info("   Learn → Monitor → Context → Agents → Intelligence → Synthesis → Trading → Mode → Report → Goals → Action")

    def _run_agent_with_comprehension(self, agent_name: str, script: str,
                                       args: List[str] = None, timeout: int = 30) -> Dict:
        logger.info(f"  🤖 [{agent_name}]...")
        r = _run_agent_script(script, args or ["--report"], timeout=timeout)
        if r.get("success") and r.get("stdout"):
            prompt = f"""وكيل [{agent_name}] أنهى.
{r['stdout'][-400:]}
جملة واحدة: ماذا وجد؟ هل تدخّل فوري؟"""
            understanding = _ask_brain(prompt, max_tokens=150)
            if understanding:
                _db_inject(f"agent_run:{agent_name}:{int(time.time())}",
                           {"agent": agent_name, "understanding": understanding,
                            "output_preview": r["stdout"][-200:]}, 0.82)
                logger.info(f"    💡 {understanding[:70]}")
        elif not r.get("success"):
            logger.warning(f"    ⚠️ فشل")
        return r

    def run_cycle(self) -> Dict:
        self._cycle += 1
        start = time.time()

        logger.info("\n" + "═"*58)
        logger.info(f"🧠 ORCHESTRATOR CYCLE #{self._cycle} | {datetime.now().strftime('%H:%M:%S')}")
        logger.info("═"*58)

        results = {}

        # ① تعلم + فهم
        try:
            results["learning"] = self.learner.run_and_comprehend()
        except Exception as e:
            logger.error(f"  ❌ Learning: {e}")
            results["learning"] = {"success": False, "error": str(e)}

        # ② مراقبة + فهم
        try:
            results["monitoring"] = self.monitor.run_and_comprehend()
        except Exception as e:
            logger.error(f"  ❌ Monitoring: {e}")
            results["monitoring"] = {"success": False, "error": str(e)}

        # ③ جلب سياق التداول (Bridge)
        trading_context = ""
        try:
            trading_context = self.trading.get_trading_context()
        except Exception as e:
            logger.warning(f"  ⚠️ trading context: {e}")

        # ④ وكلاء Sovereign
        logger.info("\n" + "─"*55)
        logger.info("🤖 [SOVEREIGN] الدماغ يختار الوكلاء...")
        logger.info("─"*55)
        brain_prompt = f"""You are NOOGH Sovereign Orchestrator.
System: Cycle {self._cycle} | Learning OK: {results.get('learning',{}).get('success')} | Monitoring: {results.get('monitoring',{}).get('understanding',{}).get('status','?')}
Choose 1-3 agents from:
- health_monitor_agent.py  - security_audit_agent.py  - log_analyzer_agent.py
- web_researcher_agent.py  - local_knowledge_harvester.py  - dependency_auditor_agent.py
- performance_profiler_agent.py  - test_runner_agent.py  - backup_agent_agent.py
- file_manager_agent.py  - pipeline_optimizer_agent.py
Return ONLY JSON array: [{{"agent_name":"Name","script":"agents/file.py"}}]"""
        brain_response = _ask_brain(brain_prompt, max_tokens=250)
        current_agents = []
        try:
            match = re.search(r'\[.*\]', brain_response, re.DOTALL)
            if match:
                for ag in json.loads(match.group(0)):
                    if isinstance(ag, dict) and "agent_name" in ag and "script" in ag:
                        sp = ag["script"]
                        if not sp.startswith("agents/"): sp = "agents/" + sp.split("/")[-1]
                        current_agents.append((ag["agent_name"], sp))
        except Exception: pass
        if not current_agents:
            current_agents = [("HealthMonitor", "agents/health_monitor_agent.py"),
                              ("LogAnalyzer",   "agents/log_analyzer_agent.py")]
        agent_results = {}
        for name, script in current_agents:
            try:
                agent_results[name] = self._run_agent_with_comprehension(name, script, timeout=25)
            except Exception as e:
                agent_results[name] = {"success": False, "error": str(e)}
        results["agents"] = {"ran": list(agent_results.keys()), "results": agent_results}
        logger.info(f"  ✅ {len(current_agents)} وكيل أنهى")

        # ⑤ دوري — Deep Scan / Distill / Evolve
        if self._cycle % 5 == 0:
            logger.info("\n🔍 [DEEP SCAN]")
            r = _run_agent_script("agents/deep_system_scanner.py", timeout=90)
            if r["success"]: logger.info("  ✅ Done")
        if self._cycle % 6 == 0:
            logger.info("\n⚗️ [DISTILLATION]")
            r = _run_agent_script("agents/memory_distiller.py", timeout=120)
            if r["success"]: logger.info("  ✅ Done")
        if self._cycle % 8 == 0:
            logger.info("\n🧬 [EVOLUTION]")
            r = _run_agent_script("agents/self_healer.py", timeout=300)
            if r["success"]: logger.info("  ✅ Done")

        # ⑥ Symbol Scorer (كل 6 دورات)
        if self._cycle % 6 == 0:
            logger.info("\n" + "─"*55)
            logger.info("🏆 [SYMBOL SCORER] تقييم الرموز...")
            logger.info("─"*55)
            results["symbol_scores"] = self.intelligence.run_symbol_scoring()

        # ⑦ Strategy Selector (كل 2 دورتين)
        if self._cycle % 2 == 0:
            logger.info("\n" + "─"*55)
            logger.info("🎯 [STRATEGY SELECTOR] تحديث الاستراتيجيات...")
            logger.info("─"*55)
            results["strategy_selection"] = self.intelligence.run_strategy_selection()

        # ⑧ Synthesis
        try:
            results["synthesis"] = self.synthesizer.synthesize(
                results.get("learning", {}),
                results.get("monitoring", {}),
                trading_context=trading_context
            )
        except Exception as e:
            logger.error(f"  ❌ Synthesis: {e}")
            results["synthesis"] = {}

        # ⑨ Trading Cycle
        trading_mode = "PAPER"  # fallback آمن قبل Mode Switcher
        try:
            results["trading"] = self.trading.run_trading_cycle(
                results.get("synthesis", {}),
                cycle_num=self._cycle,
                mode=trading_mode
            )
        except Exception as e:
            logger.error(f"  ❌ Trading: {e}")
            results["trading"] = {"error": str(e)}

        # ⑩ Mode Switcher (كل دورة — بعد التداول مباشرة)
        logger.info("\n" + "─"*55)
        logger.info("🔄 [MODE SWITCHER] تقييم الوضع...")
        logger.info("─"*55)
        current_mode = self.intelligence.run_mode_evaluation()
        results["trading_mode"] = current_mode

        # ⑪ Performance Report (كل 24 دورة)
        if self._cycle % 24 == 0:
            logger.info("\n" + "─"*55)
            logger.info("📊 [DAILY REPORT] توليد تقرير اليوم...")
            logger.info("─"*55)
            results["daily_report"] = self.intelligence.run_daily_report()

        # ⑫ تحديث الأهداف الاستراتيجية
        if self.strategy and results.get("synthesis"):
            try:
                self.strategy.review_and_update_goals(
                    results["synthesis"],
                    results.get("monitoring", {}).get("understanding", {})
                )
            except Exception as e:
                logger.error(f"  ❌ Strategy: {e}")

        # ⑬ تنفيذ القرار
        if self.decision_engine and results.get("synthesis"):
            try:
                results["action"] = self.decision_engine.execute_decision(results["synthesis"])
            except Exception as e:
                logger.error(f"  ❌ Action: {e}")

        # ── ملخص الدورة ──────────────────────────────────
        elapsed        = round(time.time() - start, 1)
        synthesis      = results.get("synthesis", {})
        action_status  = results.get("action", {}).get("status", "none")
        trading_status = results.get("trading", {}).get("trading", {}).get("status", "—")
        vol_regime     = results.get("trading", {}).get("volatility", {}).get("regime", "—")
        top_symbols    = results.get("symbol_scores", {}).get("top_symbols", [])
        strategy_pref  = results.get("strategy_selection", {}).get("preferred", [])

        logger.info("\n" + "═"*58)
        logger.info(f"✅ CYCLE #{self._cycle} DONE | {elapsed}s | Mode: {current_mode}")
        logger.info(f"   🎯 {synthesis.get('key_decision','?')[:55]}")
        logger.info(f"   ⚡ Action: {action_status}")
        logger.info(f"   📈 Trading: {trading_status} | Vol: {vol_regime}")
        if top_symbols:    logger.info(f"   🏆 Top Symbols: {top_symbols}")
        if strategy_pref:  logger.info(f"   🎯 Preferred Strategies: {strategy_pref}")
        logger.info(f"   📊 Score: {synthesis.get('overall_score','?')}")
        logger.info("═"*58)

        _db_inject("orchestrator:last_cycle", {
            "cycle":          self._cycle,
            "elapsed_sec":    elapsed,
            "timestamp":      datetime.now().isoformat(),
            "agents_ran":     results.get("agents", {}).get("ran", []),
            "synthesis":      synthesis,
            "trading_status": trading_status,
            "vol_regime":     vol_regime,
            "trading_mode":   current_mode,
            "top_symbols":    top_symbols,
            "strategy_pref":  strategy_pref,
        }, 0.96)

        return results

    def run_forever(self, interval_minutes: int = 60):
        logger.info(f"🚀 Orchestrator: كل {interval_minutes} دقيقة")
        while True:
            try:
                self.run_cycle()
            except KeyboardInterrupt:
                logger.info("⛔ Stopped"); break
            except Exception as e:
                logger.error(f"Cycle error: {e}", exc_info=True)
            logger.info(f"\n💤 Sleeping {interval_minutes}m...\n")
            time.sleep(interval_minutes * 60)


# ─── Main ───────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="NOOGH Master Orchestrator")
    p.add_argument("--once",         action="store_true")
    p.add_argument("--interval",     type=int, default=60)
    p.add_argument("--monitor-only", action="store_true")
    p.add_argument("--report",       action="store_true", help="تقرير أداء فوري")
    p.add_argument("--score",        action="store_true", help="تقييم الرموز فوري")
    args = p.parse_args()

    orch = NooghOrchestrator()

    if args.monitor_only:
        r = orch.monitor.run_and_comprehend()
        print(json.dumps(r["understanding"], ensure_ascii=False, indent=2))
    elif args.report:
        r = orch.intelligence.run_daily_report()
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif args.score:
        r = orch.intelligence.run_symbol_scoring()
        print(json.dumps({"top": r.get("top_symbols"), "avoid": r.get("avoid")}, ensure_ascii=False, indent=2))
    elif args.once:
        orch.run_cycle()
    else:
        orch.run_forever(args.interval)
