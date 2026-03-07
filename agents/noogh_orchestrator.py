#!/usr/bin/env python3
"""
NOOGH Master Orchestrator — المنسّق الرئيسي

يربط جميع الأنظمة بطبقة الفهم:

  🎬 autonomous_learner  → يتعلم → يُفهَم → يُحفظ
  🖥️  server_control     → يراقب → يُفهَم → يتصرف
  🔍 deep_scanner        → يمسح  → يُفهَم → يُخزَّن
  🧠 brain_comprehension ← طبقة الفهم المركزية

الدورة الرئيسية:
  كل ساعة:
    1. تعلم (YouTube + GitHub + arXiv + SO)
    2. فهم ما تعلمته
    3. مراقبة النظام
    4. فهم حالة النظام
    5. تركيب المعرفة الشاملة
    6. تحديد الأولويات للدورة القادمة
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


# ══════════════════════════════════════════════════════════════
# واجهة الاستيراد المحمي (لا يكسر على خطأ)
# ══════════════════════════════════════════════════════════════

def _safe_import(module_path: str, class_or_fn: str):
    """يستورد بحماية — يرجع None عند الفشل"""
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
    """يشغّل script كعملية فرعية ويلتقط نتيجته"""
    cmd = [VENV_PY, f"{SRC}/{script}"] + (args or [])
    try:
        req_env = os.environ.copy()
        req_env["PYTHONPATH"] = SRC
        r = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout, cwd=SRC, env=req_env
        )
        # If the script failed, append stderr to stdout if stdout is empty
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
    """يسأل LLM مباشرة"""
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


# ══════════════════════════════════════════════════════════════
# وحدات الأنظمة المتكاملة
# ══════════════════════════════════════════════════════════════

class LearningSystem:
    """نظام التعلم + الفهم"""

    def run_and_comprehend(self) -> Dict:
        logger.info("\n" + "─"*55)
        logger.info("🎬 [LEARNING] تعلم من 5 مصادر...")
        logger.info("─"*55)

        # تشغيل دورة تعلم واحدة
        r = _run_agent_script("agents/autonomous_learner_agent.py",
                               ["--once"], timeout=120)

        # استخراج ما تعلمه من الـ output
        learned_items = []
        tags_seen = set()
        for line in r["stdout"].split("\n"):
            if "Tags:" in line:
                tags = re.findall(r'[🎬🐙📜🟧📡]\s*\w[\w\s/]+', line)
                tags_seen.update(tags)
            if "Injected" in line or "injected" in line or "✅" in line:
                learned_items.append(line.strip()[:80])

        cycle_summary = {
            "timestamp": datetime.now().isoformat(),
            "success": r["success"],
            "tags_learned": list(tags_seen)[:10],
            "output_preview": r["stdout"][-500:],
        }

        # ── فهم ما تعلمه ──
        if r["success"] and tags_seen:
            logger.info(f"  🧠 فهم {len(tags_seen)} tags مكتسبة...")
            prompt = f"""أنت NOOGH تعلمت للتو من YouTube/GitHub/arXiv/StackOverflow.

تعلمت هذه المفاهيم: {list(tags_seen)[:8]}

من هذا الـ output:
{r['stdout'][-800:]}

أجب بـ JSON:
{{
  "what_i_learned": "خلاصة ما تعلمته في جملتين",
  "most_valuable": "أهم شيء تعلمته",
  "how_to_apply": "كيف أطبق هذا على نفسي الآن",
  "next_topic": "أهم موضوع يجب أن أتعلمه في الدورة القادمة",
  "learning_score": 0.0
}}"""
            response = _ask_brain(prompt)
            understanding = {}
            try:
                m = re.search(r'\{[\s\S]+\}', response)
                if m:
                    understanding = json.loads(m.group())
            except Exception:
                understanding = {"raw": response[:200]}

            logger.info(f"  💎 فهمت: {understanding.get('what_i_learned','?')[:60]}")
            logger.info(f"  🎯 الأهم: {understanding.get('most_valuable','?')[:60]}")
            logger.info(f"  💡 كيف أطبق: {understanding.get('how_to_apply','?')[:60]}")

            cycle_summary["understanding"] = understanding
            _db_inject("orchestrator:learning_cycle", cycle_summary, 0.93)
        else:
            logger.info(f"  ℹ️ لا تعلم جديد في هذه الدورة")
            _db_inject("orchestrator:learning_cycle", cycle_summary, 0.70)

        return cycle_summary


class MonitoringSystem:
    """نظام المراقبة + الفهم"""

    def _get_system_snapshot(self) -> Dict:
        """يجمع بيانات النظام بسرعة"""
        snap = {}

        # خدمات
        r = subprocess.run(
            "systemctl show noogh-agent noogh-neural noogh-gateway "
            "--property=ActiveState,MainPID,MemoryCurrent",
            shell=True, capture_output=True, text=True, timeout=5
        )
        services_raw = r.stdout

        active_count = services_raw.count("ActiveState=active")
        snap["services_active"] = active_count
        snap["services_raw"]    = services_raw[:400]

        # RAM
        with open("/proc/meminfo") as f:
            mem = f.read()
        total = int(re.search(r"MemTotal:\s+(\d+)", mem).group(1))
        avail = int(re.search(r"MemAvailable:\s+(\d+)", mem).group(1))
        snap["ram_pct"]  = round((total - avail) / total * 100, 1)
        snap["ram_used_gb"] = round((total-avail)/1024/1024, 1)

        # Load
        with open("/proc/loadavg") as f:
            load = f.read().split()
        snap["load_1m"] = float(load[0])

        # آخر أخطاء
        errors = []
        for log_file in ["agent_daemon_live.log", "autonomous_learner.log"]:
            try:
                path = Path(f"{SRC}/logs/{log_file}")
                if path.exists():
                    lines = path.read_text(errors="ignore").split("\n")
                    errors += [l for l in lines[-50:] if "ERROR" in l][-2:]
            except Exception:
                pass
        snap["recent_errors"] = errors[:4]
        snap["error_count"]   = len(errors)

        # ذاكرة NOOGH
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM beliefs")
            snap["beliefs_count"] = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM observations")
            snap["obs_count"] = cur.fetchone()[0]
            conn.close()
        except Exception:
            pass

        return snap

    def run_and_comprehend(self) -> Dict:
        logger.info("\n" + "─"*55)
        logger.info("🖥️  [MONITORING] مراقبة + فهم حالة النظام...")
        logger.info("─"*55)

        snap = self._get_system_snapshot()

        logger.info(
            f"  📊 خدمات: {snap['services_active']}/3 | "
            f"RAM: {snap['ram_used_gb']}GB ({snap['ram_pct']}%) | "
            f"Load: {snap['load_1m']}"
        )
        if snap['recent_errors']:
            logger.warning(f"  ⚠️ أخطاء: {len(snap['recent_errors'])}")
            for e in snap['recent_errors'][:2]:
                logger.warning(f"     {e[:80]}")

        # ── فهم الحالة ──
        prompt = f"""أنت NOOGH تراقب نفسك الآن.

حالة الخدمات ({snap['services_active']}/3 نشطة):
{snap['services_raw'][:300]}

RAM: {snap['ram_pct']}% ({snap['ram_used_gb']} GB)
Load: {snap['load_1m']}
ذاكرتي: {snap.get('beliefs_count','?')} beliefs | {snap.get('obs_count','?')} observations
أخطاء الآن: {snap['error_count']}
{chr(10).join(snap['recent_errors'][:2]) if snap['recent_errors'] else 'لا أخطاء'}

قيّم حالتي وأجب بـ JSON:
{{
  "status": "healthy|warning|critical",
  "status_score": 0.0,
  "biggest_concern": "أكبر مشكلة الآن أو 'none'",
  "action_needed": true,
  "action": "ما يجب فعله الآن",
  "prediction": "ما أتوقع حدوثه خلال ساعة"
}}"""

        response = _ask_brain(prompt)
        understanding = {}
        try:
            m = re.search(r'\{[\s\S]+\}', response)
            if m:
                understanding = json.loads(m.group())
        except Exception:
            understanding = {"raw": response[:200]}

        logger.info(f"  🩺 الحالة: {understanding.get('status','?')} ({understanding.get('status_score','?')})")
        logger.info(f"  🔮 توقع: {understanding.get('prediction','?')[:60]}")
        if understanding.get("action_needed"):
            logger.info(f"  ⚡ إجراء مطلوب: {understanding.get('action','?')[:60]}")

        result = {"snapshot": snap, "understanding": understanding}
        _db_inject("orchestrator:system_monitoring", result, 0.95)

        # تعافٍ ذاتي إذا كان النظام في خطر
        if understanding.get("status") == "critical":
            logger.warning("  🚨 النظام في حالة حرجة — تعافٍ ذاتي...")
            self._self_heal(snap, understanding)

        return result

    def _self_heal(self, snap: Dict, understanding: Dict):
        """تعافٍ ذاتي تلقائي"""
        concern = understanding.get("biggest_concern", "")
        # إعادة تشغيل الخدمة إذا كانت متوقفة
        if "noogh-agent" in concern or snap["services_active"] < 3:
            logger.info("  🔄 محاولة إعادة تشغيل خدمات NOOGH...")
            subprocess.run(
                f"echo '107194' | sudo -S systemctl restart noogh-agent",
                shell=True, capture_output=True, timeout=30
            )


class KnowledgeSynthesizer:
    """مركب المعرفة — يجمع كل ما فهمه ويستخلص رؤية شاملة وتوجيه استراتيجي بناءً على الأهداف"""

    def synthesize(self, learning_result: Dict, monitoring_result: Dict) -> Dict:
        logger.info("\n" + "─"*55)
        logger.info("🔮 [SYNTHESIS] تركيب المعرفة الشاملة وتوجيه المسار...")
        logger.info("─"*55)

        # ما تعلمه وما يعرفه عن نظامه
        l_understanding = learning_result.get("understanding", {})
        m_understanding = monitoring_result.get("understanding", {})
        m_snap          = monitoring_result.get("snapshot", {})

        # أهم الـ beliefs الحالية، بالإضافة للأهداف الاستراتيجية
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()
            
            # جلب الأهداف الاستراتيجية
            cur.execute("SELECT value FROM beliefs WHERE key='system:strategic_goals'")
            row = cur.fetchone()
            strategic_goals_str = row[0] if row else "{'short_term': [], 'long_term': []}"
            
            # جلب أهم المعتقدات
            cur.execute(
                "SELECT key, utility_score FROM beliefs "
                "WHERE key != 'system:strategic_goals' "
                "ORDER BY utility_score DESC LIMIT 8"
            )
            top_beliefs = [{"key": r[0][:40], "u": round(r[1], 2)} for r in cur.fetchall()]
            conn.close()
        except Exception as e:
            logger.error(f"  DB Error syntheisizing: {e}")
            top_beliefs = []
            strategic_goals_str = "{}"

        prompt = f"""أنت NOOGH — تقرير الدورة الشاملة وقرار المسار الجديد.

⚠️ أهدافك الاستراتيجية الحاكمة:
{strategic_goals_str}

ما تعلمته:
  أهم شيء: {l_understanding.get('most_valuable','لا شيء جديد')}
  كيف أطبقه: {l_understanding.get('how_to_apply','؟')}
  الموضوع القادم: {l_understanding.get('next_topic','؟')}

حالة نظامي:
  الحالة: {m_understanding.get('status','؟')} ({m_understanding.get('status_score','؟')})
  أكبر مشكلة: {m_understanding.get('biggest_concern','none')}
  توقع: {m_understanding.get('prediction','؟')}

أهم ما أؤمن به الآن:
{json.dumps([f"{b['key']} (u={b['u']})" for b in top_beliefs[:5]], ensure_ascii=False)}

الآن: بناءً على "أهدافك الاستراتيجية" بشكل أساسي والمشكلات الحالية:
1. ما القرارات المحددة التي يجب اتخاذها الآن لتحقيق الأهداف قصيرة الأمد؟
2. أين تركز جهودك في الساعة القادمة؟
3. هل تتقدم نحو أهدافك بعيدة المدى بشكل صحيح؟

أجب بـ JSON:
{{
  "key_decision": "القرار الأهم",
  "next_hour_focus": "ما أفعله في الساعة القادمة",
  "is_evolving_correctly": true,
  "self_insight": "إدراك ذاتي عميق جديد عن أدائي ومساري",
  "overall_score": 0.0
}}"""

        response = _ask_brain(prompt, max_tokens=500)
        synthesis = {}
        try:
            m = re.search(r'\{[\s\S]+\}', response)
            if m:
                synthesis = json.loads(m.group())
        except Exception:
            synthesis = {"raw": response[:200]}

        logger.info(f"  🎯 القرار الاستراتيجي: {synthesis.get('key_decision','?')[:65]}")
        logger.info(f"  ⏰ التركيز القادم: {synthesis.get('next_hour_focus','?')[:65]}")
        logger.info(f"  💭 وعي ذاتي: {synthesis.get('self_insight','?')[:65]}")
        logger.info(f"  📈 تطور نحو الأهداف: {'✅' if synthesis.get('is_evolving_correctly') else '⚠️'}")

        _db_inject("orchestrator:synthesis", synthesis, 0.98)
        return synthesis


# ══════════════════════════════════════════════════════════════
# المنسّق الرئيسي
# ══════════════════════════════════════════════════════════════

class NooghOrchestrator:
    """القائد الذي يربط كل شيء"""

    def __init__(self):
        self.learner    = LearningSystem()
        self.monitor    = MonitoringSystem()
        self.synthesizer = KnowledgeSynthesizer()
        
        # استدعاء محرك القرار 
        try:
            from agents.decision_engine import DecisionEngine
            self.decision_engine = DecisionEngine()
        except ImportError:
            self.decision_engine = None
            logger.warning("  ⚠️ DecisionEngine not found. Actions will not be executed.")

        # استدعاء مشرف الاستراتيجية
        try:
            from agents.strategic_goals import StrategicGoalsSupervisor
            self.strategy = StrategicGoalsSupervisor()
        except ImportError:
            self.strategy = None
            logger.warning("  ⚠️ StrategicGoalsSupervisor not found.")

        self._cycle = 0
        logger.info("🤖 NOOGH Orchestrator initialized")
        logger.info("   Learn ←→ Monitor ←→ Agents ←→ Synthesis ←→ Strategy ←→ Action")


    def _run_agent_with_comprehension(self, agent_name: str,
                                       script: str, args: List[str] = None,
                                       timeout: int = 30) -> Dict:
        """يشغّل وكيلاً ويمرر نتيجته على طبقة الفهم"""
        logger.info(f"  🤖 [{agent_name}]...")
        r = _run_agent_script(script, args or ["--report"], timeout=timeout)

        if r.get("success") and r.get("stdout"):
            prompt = f"""وكيل NOOGH [{agent_name}] أنهى مهمته.

نتيجته:
{r['stdout'][-400:]}

في جملة واحدة:
1. ماذا وجد؟
2. هل يحتاج تدخل فوري؟"""
            understanding = _ask_brain(prompt, max_tokens=150)
            if understanding:
                _db_inject(
                    f"agent_run:{agent_name}:{int(time.time())}",
                    {"agent": agent_name, "understanding": understanding,
                     "output_preview": r["stdout"][-200:]},
                    utility=0.82
                )
                logger.info(f"    💡 {understanding[:70]}")
        elif not r.get("success"):
            logger.warning(f"    ⚠️ فشل أو لم ينشئ تقريراً")

        return r

    def run_cycle(self) -> Dict:
        self._cycle += 1
        start = time.time()

        logger.info("\n" + "═"*58)
        logger.info(f"🧠 ORCHESTRATOR CYCLE #{self._cycle} | {datetime.now().strftime('%H:%M:%S')}")
        logger.info("═"*58)

        results = {}

        # ① التعلم + الفهم
        try:
            results["learning"] = self.learner.run_and_comprehend()
        except Exception as e:
            logger.error(f"  ❌ Learning error: {e}")
            results["learning"] = {"success": False, "error": str(e)}

        # ② المراقبة + الفهم
        try:
            results["monitoring"] = self.monitor.run_and_comprehend()
        except Exception as e:
            logger.error(f"  ❌ Monitoring error: {e}")
            results["monitoring"] = {"success": False, "error": str(e)}

        # ③ الوكلاء المتخصصون — اختيار من الدماغ (Sovereign Orchestration)
        logger.info("\n" + "─"*55)
        logger.info("🤖 [SOVEREIGN AGENTS] الدماغ يختار الوكلاء لهذه الدورة...")
        logger.info("─"*55)

        # نجمع حالة النظام الحالية لمساعدة الدماغ على اتخاذ القرار
        system_context = f"Cycle: {self._cycle}\n"
        system_context += f"Learning Status: {results.get('learning', {}).get('success', False)}\n"
        system_context += f"Monitoring Status: {results.get('monitoring', {}).get('success', False)}\n"
        system_context += f"Monitoring Understanding: {results.get('monitoring', {}).get('understanding', 'None')}\n"

        prompt = f"""You are the Sovereign Orchestrator of NOOGH.
Based on the current system context, which ONE to THREE local agents should be executed right now?
Available Agents:
- health_monitor_agent.py (Check system health & RAM)
- security_audit_agent.py (Scan for vulnerabilities)
- log_analyzer_agent.py (Read recent logs for errors)
- web_researcher_agent.py (Search the web for topics)
- local_knowledge_harvester.py (Scan local files for knowledge)
- dependency_auditor_agent.py (Check pip packages)
- tiktok_auditor_agent.py (Analyze TikTok trends)
- performance_profiler_agent.py (Profile python scripts)
- test_runner_agent.py (Run pytest)
- pipeline_optimizer_agent.py (Optimize code pipelines)
- rapid_prototyping_agent.py (Write quick python tests)
- backup_agent_agent.py (Backup the system)
- file_manager_agent.py (Organize files)

System Context:
{system_context}

Return ONLY a valid JSON array of objects representing the agents to run. 
Each object must have "agent_name" (a readable name) and "script" (the path starting with 'agents/').
Example:
[
  {{"agent_name": "HealthMonitor", "script": "agents/health_monitor_agent.py"}},
  {{"agent_name": "LocalHarvester", "script": "agents/local_knowledge_harvester.py"}}
]
"""
        brain_response = _ask_brain(prompt, max_tokens=300)
        
        current_agents = []
        try:
            match = re.search(r'\[.*\]', brain_response, re.DOTALL)
            if match:
                selected_agents = json.loads(match.group(0))
                for ag in selected_agents:
                    if isinstance(ag, dict) and "agent_name" in ag and "script" in ag:
                        # Ensure the script starts with agents/
                        script_path = ag["script"]
                        if not script_path.startswith("agents/"):
                            script_path = "agents/" + script_path.split("/")[-1]
                        current_agents.append((ag["agent_name"], script_path))
        except Exception as e:
            logger.error(f"  ❌ Failed to parse Brain agent selection: {e}")
            
        if not current_agents:
            logger.warning("  ⚠️ Brain returned invalid JSON or empty array. Falling back to default.")
            current_agents = [
                ("HealthMonitor", "agents/health_monitor_agent.py"),
                ("LogAnalyzer",   "agents/log_analyzer_agent.py")
            ]
            
        logger.info(f"  🧠 Brain selected {len(current_agents)} agents to run:")
        for name, script_path in current_agents:
            logger.info(f"     - {name} ({script_path})")

        agent_results = {}
        for agent_name, script in current_agents:
            try:
                agent_results[agent_name] = self._run_agent_with_comprehension(
                    agent_name, script, timeout=25
                )
            except Exception as e:
                logger.warning(f"    ⚠️ {agent_name}: {e}")
                agent_results[agent_name] = {"success": False, "error": str(e)}

        results["agents"] = {
            "group": "sovereign",
            "ran": list(agent_results.keys()),
            "results": agent_results,
        }
        logger.info(f"  ✅ {len(current_agents)} وكيل أنهى مهمته بناءً على أوامر الدماغ")

        # ④ المسح العميق كل 5 دورات والتنظيف كل 6 دورات
        if self._cycle % 5 == 0:
            logger.info("\n🔍 [DEEP SCAN] مسح شامل كل 5 دورات...")
            r = _run_agent_script("agents/deep_system_scanner.py", timeout=90)
            if r["success"]:
                logger.info("  ✅ Deep scan complete")
                _ask_brain(f"ما أهم ما وجده هذا المسح:\n{r['stdout'][-500:]}")
                
        if self._cycle % 6 == 0:
            logger.info("\n⚗️ [DISTILLATION] تقطير وتنظيف الذاكرة كل 6 دورات...")
            r = _run_agent_script("agents/memory_distiller.py", timeout=120)
            if r["success"]:
                logger.info("  ✅ Memory distilled successfully")
                
        # ⑤ التطور الذاتي (Self-Healing / Refactoring) كل 8 دورات
        if self._cycle % 8 == 0:
            logger.info("\n🧬 [EVOLUTION] فحص الأكواد وتحسين الذات...")
            r = _run_agent_script("agents/self_healer.py", timeout=300)
            if r["success"]:
                logger.info("  ✅ Self-Healing cycle finished")
            else:
                logger.warning(f"  ⚠️ Self-Healing returned non-success (or timed out)")

        # ⑥ التركيب الشامل
        try:
            results["synthesis"] = self.synthesizer.synthesize(
                results.get("learning", {}),
                results.get("monitoring", {})
            )
        except Exception as e:
            logger.error(f"  ❌ Synthesis error: {e}")
            results["synthesis"] = {}
            
        # ⑥ تحديث الأهداف الاستراتيجية (Strategy)
        if self.strategy and results.get("synthesis"):
            try:
                mon_state = results.get("monitoring", {}).get("understanding", {})
                self.strategy.review_and_update_goals(results["synthesis"], mon_state)
            except Exception as e:
                logger.error(f"  ❌ Strategy update error: {e}")
            
        # ⑦ التنفيذ (Action)

        if self.decision_engine and results.get("synthesis"):
            try:
                action_result = self.decision_engine.execute_decision(results["synthesis"])
                results["action"] = action_result
            except Exception as e:
                logger.error(f"  ❌ Decision Execution error: {e}")

        # ── ملخص الدورة ──
        elapsed = round(time.time() - start, 1)
        synthesis = results.get("synthesis", {})
        action_status = results.get("action", {}).get("status", "none")
        logger.info("\n" + "═"*58)
        logger.info(f"✅ CYCLE #{self._cycle} DONE | {elapsed}s")
        logger.info(f"   🎯 {synthesis.get('key_decision','?')[:55]}")
        logger.info(f"   ⚡ Action Status: {action_status}")
        logger.info(f"   📈 Score: {synthesis.get('overall_score','?')}")
        logger.info("═"*58)

        _db_inject("orchestrator:last_cycle", {
            "cycle": self._cycle,
            "elapsed_sec": elapsed,
            "timestamp": datetime.now().isoformat(),
            "agents_ran": results.get("agents", {}).get("ran", []),
            "synthesis": synthesis,
        }, 0.96)

        return results

    def run_forever(self, interval_minutes: int = 60):
        """يعمل إلى الأبد في حلقة"""
        logger.info(f"🚀 Orchestrator loop: every {interval_minutes} min")
        while True:
            try:
                self.run_cycle()
            except KeyboardInterrupt:
                logger.info("⛔ Stopped")
                break
            except Exception as e:
                logger.error(f"Cycle error: {e}", exc_info=True)

            logger.info(f"\n💤 Sleeping {interval_minutes} minutes...\n")
            time.sleep(interval_minutes * 60)


# ─── Main ─────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="NOOGH Master Orchestrator")
    p.add_argument("--once",     action="store_true", help="دورة واحدة فقط")
    p.add_argument("--interval", type=int, default=60, help="كل N دقيقة")
    p.add_argument("--monitor-only", action="store_true", help="مراقبة فقط")
    args = p.parse_args()

    orch = NooghOrchestrator()

    if args.monitor_only:
        r = orch.monitor.run_and_comprehend()
        print(json.dumps(r["understanding"], ensure_ascii=False, indent=2))
    elif args.once:
        orch.run_cycle()
    else:
        orch.run_forever(args.interval)
