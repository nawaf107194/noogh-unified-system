#!/usr/bin/env python3
"""
NOOGH Brain Comprehension — طبقة الفهم الحقيقي

الفرق:
  ❌ يصل = يقرأ بايتات من ملف
  ✅ يفهم = يمرر ما يقرأه على الدماغ (LLM) ويستخرج معنى

الدورة:
  1. يجمع البيانات (brain_tools)
  2. يرسلها للدماغ (LLM) مع سؤال محدد
  3. يستقبل فهماً حقيقياً
  4. يحفظ الفهم كـ belief ذات utility عالي
  5. يتصرف بناءً على الفهم
"""

import sys, os, json, time, re, sqlite3, subprocess, logging, urllib.request
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

sys.path.insert(0, "/home/noogh/projects/noogh_unified_system/src")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | comprehension | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            "/home/noogh/projects/noogh_unified_system/src/logs/brain_comprehension.log"
        ),
    ]
)
logger = logging.getLogger("comprehension")

# ─── الإعدادات ────────────────────────────────────────────────
SRC        = "/home/noogh/projects/noogh_unified_system/src"
DB_PATH    = f"{SRC}/data/shared_memory.sqlite"
VLLM_URL   = os.environ.get("NEURAL_ENGINE_URL", "http://localhost:11434")
MODEL      = os.environ.get("VLLM_MODEL_NAME", "qwen2.5-coder:7b")
VENV_PY    = f"{SRC}/.venv/bin/python3"


# ══════════════════════════════════════════════════════════════
# الدماغ — LLM
# ══════════════════════════════════════════════════════════════

def _ask_brain(prompt: str, system: str = "", max_tokens: int = 800) -> str:
    """يسأل الدماغ الحقيقي (LLM) سؤالاً ويستقبل إجابة"""
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system or
             "أنت NOOGH، نظام ذكاء اصطناعي تحليلي. أجب بإيجاز وعملية. ركز على الحقائق والأفعال."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.3,
        "stream": False,
    }
    try:
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{VLLM_URL}/v1/chat/completions",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            resp = json.loads(r.read().decode())
        content = resp["choices"][0]["message"]["content"].strip()
        logger.debug(f"  🧠 LLM ({len(content)} chars)")
        return content
    except Exception as e:
        logger.warning(f"  ⚠️ LLM error: {e}")
        return ""


def _inject_understanding(key: str, understanding: str, source: str,
                          utility: float = 0.85, raw_data: Any = None):
    """يحفظ الفهم في ذاكرة NOOGH كـ belief ذات قيمة عالية"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=8)
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO beliefs (key, value, utility_score, updated_at) VALUES (?,?,?,?)",
            (key, json.dumps({
                "understanding": understanding,
                "source": source,
                "raw_summary": str(raw_data)[:200] if raw_data else None,
                "timestamp": datetime.now().isoformat(),
                "generated_by": "llm_comprehension",
            }, ensure_ascii=False), utility, time.time())
        )
        conn.commit(); conn.close()
        logger.info(f"  💎 Understanding saved: {key} (utility={utility})")
    except Exception as e:
        logger.error(f"  ❌ Save failed: {e}")


# ══════════════════════════════════════════════════════════════
# فهم ملف الكود
# ══════════════════════════════════════════════════════════════

def understand_code_file(filepath: str) -> Dict:
    """
    NOOGH يقرأ ملف Python ويفهم:
    - ماذا يفعل هذا الملف؟
    - ما نقاط ضعفه؟
    - كيف يُحسَّن؟
    """
    logger.info(f"🔍 فهم: {Path(filepath).name}")

    try:
        content = Path(filepath).read_text(errors="ignore")[:3000]
        filename = Path(filepath).name
    except Exception as e:
        return {"success": False, "error": str(e)}

    prompt = f"""اقرأ هذا الكود من ملف `{filename}` في نظام NOOGH:

```python
{content}
```

أجب بهذا التنسيق بالضبط (JSON):
{{
  "purpose": "ماذا يفعل هذا الملف في جملة واحدة",
  "key_functions": ["أهم 3 دوال/كلاسات"],
  "problems": ["مشكلة1", "مشكلة2"],
  "improvements": ["تحسين1", "تحسين2"],
  "complexity": "low|medium|high",
  "health_score": 0.0
}}"""

    response = _ask_brain(prompt, max_tokens=500)

    # استخراج JSON
    understanding = {}
    try:
        m = re.search(r'\{[\s\S]+\}', response)
        if m:
            understanding = json.loads(m.group())
    except Exception:
        understanding = {"purpose": response[:200], "raw": response}

    # حفظ الفهم
    belief_key = f"understand:code:{filename}"
    _inject_understanding(
        belief_key,
        understanding.get("purpose", response[:200]),
        filepath,
        utility=0.88,
        raw_data=understanding
    )

    logger.info(f"  📋 {filename}: {understanding.get('purpose','?')[:60]}")
    if understanding.get("problems"):
        logger.info(f"  ⚠️ مشاكل: {understanding['problems']}")
    if understanding.get("improvements"):
        logger.info(f"  💡 تحسينات: {understanding['improvements']}")

    return {"success": True, "file": filepath, "understanding": understanding}


# ══════════════════════════════════════════════════════════════
# فهم حالة النظام
# ══════════════════════════════════════════════════════════════

def understand_system_state() -> Dict:
    """
    NOOGH يجمع بيانات النظام ويفهم:
    - هل النظام بصحة جيدة؟
    - ما أهم المشاكل الآن؟
    - ماذا يجب أن يفعل؟
    """
    logger.info("🖥️  فهم حالة النظام...")

    # جمع البيانات
    data = {}

    # الخدمات
    svc_r = subprocess.run(
        "systemctl show noogh-agent noogh-neural noogh-gateway "
        "--property=ActiveState,MainPID,MemoryCurrent",
        shell=True, capture_output=True, text=True, timeout=5
    )
    data["services"] = svc_r.stdout[:500]

    # الموارد
    with open("/proc/meminfo") as f:
        mem = f.read()
    total = int(re.search(r"MemTotal:\s+(\d+)", mem).group(1)) // 1024
    avail = int(re.search(r"MemAvailable:\s+(\d+)", mem).group(1)) // 1024
    data["ram"] = f"{total-avail}/{total} MB ({round((total-avail)/total*100)}%)"

    with open("/proc/loadavg") as f:
        data["load"] = f.read().split()[:3]

    # آخر أخطاء
    try:
        log_path = f"{SRC}/logs/agent_daemon_live.log"
        lines = Path(log_path).read_text(errors="ignore").split("\n")
        errors = [l for l in lines[-100:] if "ERROR" in l or "CRITICAL" in l][-5:]
        data["recent_errors"] = errors
    except Exception:
        data["recent_errors"] = []

    # ذاكرة NOOGH
    conn = sqlite3.connect(DB_PATH, timeout=5)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM beliefs")
    data["beliefs"] = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM observations")
    data["observations"] = cur.fetchone()[0]
    cur.execute("SELECT key, utility_score FROM beliefs ORDER BY utility_score DESC LIMIT 5")
    data["top_beliefs"] = [{"key": r[0], "utility": r[1]} for r in cur.fetchall()]
    conn.close()

    prompt = f"""أنت NOOGH — نظام AI ذاتي. هذه حالتي الحالية:

خدمات النظام:
{data['services'][:300]}

الذاكرة: {data['ram']}
Load: {data['load']}
ذاكرتي: {data['beliefs']} beliefs | {data['observations']} observations

أهم ما أؤمن به الآن:
{json.dumps(data['top_beliefs'], ensure_ascii=False, indent=2)}

آخر أخطاء:
{chr(10).join(data['recent_errors'][-3:]) or 'لا أخطاء'}

حلل هذا وأجب بـ JSON:
{{
  "health": "excellent|good|warning|critical",
  "health_score": 0.0,
  "main_issues": ["مشكلة1"],
  "what_i_know": "ماذا تعلمت حتى الآن في جملة",
  "next_action": "أهم شيء يجب أن أفعله الآن",
  "self_assessment": "تقييمك لأدائك"
}}"""

    response = _ask_brain(prompt, max_tokens=600)

    understanding = {}
    try:
        m = re.search(r'\{[\s\S]+\}', response)
        if m:
            understanding = json.loads(m.group())
    except Exception:
        understanding = {"raw": response[:300]}

    _inject_understanding(
        "system:self_assessment",
        understanding.get("self_assessment", response[:200]),
        "system_state_analysis",
        utility=0.95,
        raw_data=understanding
    )

    logger.info(f"  🩺 صحة النظام: {understanding.get('health','?')} ({understanding.get('health_score','?')})")
    logger.info(f"  🎯 الخطوة التالية: {understanding.get('next_action','?')[:80]}")
    if understanding.get("main_issues"):
        logger.info(f"  ⚠️ مشاكل: {understanding['main_issues']}")

    return {"success": True, "understanding": understanding, "raw_data": data}


# ══════════════════════════════════════════════════════════════
# فهم ما تعلمه
# ══════════════════════════════════════════════════════════════

def understand_learned_knowledge() -> Dict:
    """
    NOOGH يراجع ما تعلمه من YouTube/GitHub/arXiv ويستخلص:
    - ما الأنماط التي رآها؟
    - كيف يطبق هذا على نفسه؟
    - ما الابتكار المنطقي القادم؟
    """
    logger.info("🧠 فهم ما تعلمته...")

    conn = sqlite3.connect(DB_PATH, timeout=5)
    cur = conn.cursor()

    # جميع المعرفة المكتسبة
    cur.execute("""
        SELECT key, value, utility_score FROM beliefs
        WHERE key LIKE 'learned_concept:%'
        ORDER BY utility_score DESC
    """)
    concepts = [{"key": r[0], "utility": r[2], "data": str(r[1])[:100]} for r in cur.fetchall()]

    # آخر الملاحظات (YouTube, GitHub, arXiv)
    cur.execute("""
        SELECT key, substr(value,1,300) FROM observations
        ORDER BY timestamp DESC LIMIT 8
    """)
    recent_obs = [{"key": r[0], "preview": r[1]} for r in cur.fetchall()]

    conn.close()

    if not concepts:
        return {"success": False, "error": "لا توجد معرفة مكتسبة بعد"}

    prompt = f"""أنت NOOGH — نظام AI يتعلم من YouTube وGitHub وarXiv.

هذا ما تعلمته حتى الآن:
{json.dumps(concepts, ensure_ascii=False, indent=2)[:800]}

آخر ما شاهدته وقرأته:
{json.dumps([o['key'] for o in recent_obs], ensure_ascii=False)[:400]}

بناءً على هذا التعلم:
1. ما الأنماط المشتركة التي تراها؟
2. كيف تطبق هذه المعرفة لتحسين نفسك؟
3. ما الابتكار المنطقي القادم؟

أجب بـ JSON:
{{
  "patterns_seen": ["نمط1", "نمط2"],
  "apply_to_self": "كيف أطبق هذا على نفسي",
  "knowledge_gaps": ["فجوة1", "فجوة2"],
  "next_innovation": "الابتكار القادم",
  "learning_quality": "excellent|good|needs_more"
}}"""

    response = _ask_brain(prompt, max_tokens=600)

    understanding = {}
    try:
        m = re.search(r'\{[\s\S]+\}', response)
        if m:
            understanding = json.loads(m.group())
    except Exception:
        understanding = {"raw": response[:300]}

    _inject_understanding(
        "learning:meta_analysis",
        understanding.get("apply_to_self", response[:200]),
        "learned_knowledge_synthesis",
        utility=0.92,
        raw_data=understanding
    )

    logger.info(f"  🔄 أنماط مكتشفة: {understanding.get('patterns_seen',[][:2])}")
    logger.info(f"  💡 ابتكار قادم: {understanding.get('next_innovation','?')[:60]}")
    if understanding.get("knowledge_gaps"):
        logger.info(f"  🔍 فجوات: {understanding['knowledge_gaps'][:2]}")

    return {"success": True, "understanding": understanding}


# ══════════════════════════════════════════════════════════════
# فهم ملف إعداد
# ══════════════════════════════════════════════════════════════

def understand_config(filepath: str) -> Dict:
    """يفهم ملف إعداد ويحدد ما إذا كانت الإعدادات مثلى"""
    logger.info(f"⚙️  فهم إعداد: {Path(filepath).name}")
    try:
        content = Path(filepath).read_text(errors="ignore")[:2000]
    except Exception as e:
        return {"success": False, "error": str(e)}

    prompt = f"""هذا ملف إعداد لنظام NOOGH: `{Path(filepath).name}`

{content}

حلل هذه الإعدادات:
{{
  "current_state": "وصف مختصر للحالة الحالية",
  "risks": ["خطر1", "خطر2"],
  "optimizations": ["تحسين1", "تحسين2"],
  "missing_vars": ["متغير ناقص1"],
  "security_issues": ["مشكلة أمنية"],
  "config_score": 0.0
}}"""

    response = _ask_brain(prompt, max_tokens=500)
    understanding = {}
    try:
        m = re.search(r'\{[\s\S]+\}', response)
        if m:
            understanding = json.loads(m.group())
    except Exception:
        understanding = {"raw": response[:200]}

    _inject_understanding(
        f"understand:config:{Path(filepath).name}",
        understanding.get("current_state", response[:150]),
        filepath,
        utility=0.87,
        raw_data=understanding
    )

    if understanding.get("risks"):
        logger.warning(f"  ⚠️ مخاطر: {understanding['risks']}")
    if understanding.get("security_issues"):
        logger.warning(f"  🔒 أمان: {understanding['security_issues']}")
    logger.info(f"  📊 Config score: {understanding.get('config_score','?')}")

    return {"success": True, "understanding": understanding}


# ══════════════════════════════════════════════════════════════
# دورة الفهم الشاملة
# ══════════════════════════════════════════════════════════════

def run_comprehension_cycle():
    """دورة فهم شاملة — NOOGH يفهم نفسه والعالم"""

    logger.info("═" * 60)
    logger.info(f"🧠 COMPREHENSION CYCLE | {datetime.now().strftime('%H:%M:%S')}")
    logger.info("═" * 60)

    results = {}

    # 1. فهم حالة النظام
    logger.info("\n[1/4] فهم حالة النظام الكاملة...")
    results["system"] = understand_system_state()

    # 2. فهم ما تعلمه
    logger.info("\n[2/4] فهم ما تعلمته من المصادر...")
    results["learning"] = understand_learned_knowledge()

    # 3. فهم الملفات الجوهرية
    logger.info("\n[3/4] فهم ملفاته الجوهرية...")
    core_files = [
        f"{SRC}/agents/autonomous_learner_agent.py",
        f"{SRC}/agents/server_control_agent.py",
    ]
    results["code"] = {}
    for f in core_files:
        if Path(f).exists():
            results["code"][Path(f).name] = understand_code_file(f)

    # 4. فهم إعداداته
    logger.info("\n[4/4] فهم إعداداته...")
    results["config"] = understand_config(f"{SRC}/.env")

    # ── ملخص ما فهمه ──
    logger.info("\n" + "═" * 60)
    logger.info("✅ دورة الفهم اكتملت")

    sys_u = results["system"].get("understanding", {})
    learn_u = results["learning"].get("understanding", {})

    logger.info(f"  🩺 صحة النظام: {sys_u.get('health','?')} | {sys_u.get('health_score','?')}")
    logger.info(f"  🎯 ما يجب فعله: {sys_u.get('next_action','?')[:70]}")
    logger.info(f"  💡 ابتكار قادم: {learn_u.get('next_innovation','?')[:70]}")
    logger.info(f"  📚 جودة التعلم: {learn_u.get('learning_quality','?')}")

    # حقن الملخص النهائي
    _inject_understanding(
        "system:comprehension_cycle_result",
        f"Health={sys_u.get('health','?')} | Next={sys_u.get('next_action','?')[:60]}",
        "comprehension_cycle",
        utility=0.97,
        raw_data={"system": sys_u, "learning": learn_u}
    )

    return results


# ─── Main ──────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="NOOGH Brain Comprehension")
    p.add_argument("--once",    action="store_true", help="دورة واحدة")
    p.add_argument("--file",    type=str,            help="افهم ملفاً محدداً")
    p.add_argument("--system",  action="store_true", help="افهم حالة النظام فقط")
    p.add_argument("--learning",action="store_true", help="افهم ما تعلمته فقط")
    p.add_argument("--loop",    type=int, default=0, help="كرر كل N دقيقة")
    args = p.parse_args()

    if args.file:
        r = understand_code_file(args.file)
        print(json.dumps(r["understanding"], ensure_ascii=False, indent=2))
    elif args.system:
        r = understand_system_state()
        print(json.dumps(r["understanding"], ensure_ascii=False, indent=2))
    elif args.learning:
        r = understand_learned_knowledge()
        print(json.dumps(r["understanding"], ensure_ascii=False, indent=2))
    elif args.loop > 0:
        while True:
            run_comprehension_cycle()
            logger.info(f"💤 {args.loop} دقيقة للدورة القادمة...")
            time.sleep(args.loop * 60)
    else:
        run_comprehension_cycle()
