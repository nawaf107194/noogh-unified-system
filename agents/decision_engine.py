#!/usr/bin/env python3
"""
NOOGH Decision Engine — محرك القرار والتنفيذ
------------------------------------------------------
يأخذ القرارات الاستراتيجية التي يصدرها المنسق (Orchestrator)،
ويحولها إلى قائمة أفعال حقيقية عبر أدوات الدماغ (brain_tools).

يفهم → يقرر → **يتصرف**
"""

import sys, os, json, time, sqlite3, logging, re
from typing import Dict, Any, List
sys.path.insert(0, "/home/noogh/projects/noogh_unified_system/src")

from unified_core.brain_tools import use_tool, list_tools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | decision | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            "/home/noogh/projects/noogh_unified_system/src/logs/decision_engine.log"
        ),
    ]
)
logger = logging.getLogger("decision")

SRC = "/home/noogh/projects/noogh_unified_system/src"
DB_PATH = f"{SRC}/data/shared_memory.sqlite"
VLLM_URL = os.environ.get("NEURAL_ENGINE_URL", "http://localhost:11434")
MODEL = os.environ.get("VLLM_MODEL_NAME", "qwen2.5-coder:7b")


def _ask_brain_with_tools(prompt: str, tools_schema: List[Dict]) -> Dict:
    """يسأل LLM ويجبره على الاستجابة بنداء أداة (Tool Call) أو لا شيء"""
    import urllib.request
    
    # تحويل schema الأدوات لصيغة يسهل على Qwen فهمها في الـ Prompt
    tools_str = json.dumps(tools_schema, ensure_ascii=False, indent=2)
    
    system_prompt = f"""أنت NOOGH، الذكاء الاصطناعي السيادي الحاكم للنظام.
لقد تم اتخاذ "قرار". مهمتك هي تنفيذ هذا القرار باختيار أداة واحدة من الأدوات المتاحة وإرجاع المتغيرات (JSON فقط).
إذا لم يكن القرار يحتاج إلى أفعال مباشرة على النظام (مثل: "الاستمرار في المراقبة")، أرجع أداة فارغة.

ملاحظة هامة للمسارات:
دائماً استخدم مسارات كاملة ومطلقة تبدأ بـ:
/home/noogh/projects/noogh_unified_system/src/

الأدوات المتاحة لك:
{tools_str}

قاعدة صارمة: أجب فقط بتنسيق JSON التالي ولا شيء غيره:
{{
  "thought": "تفكيرك المنطقي لاختيار الأداة",
  "tool_name": "اسم_الأداة أو فارغ",
  "arguments": {{"arg1": "value1"}}
}}"""

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500,
        "temperature": 0.1,
        "stream": False,
    }
    try:
        body = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{VLLM_URL}/v1/chat/completions", data=body,
            headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(req, timeout=45) as r:
            content = json.loads(r.read())["choices"][0]["message"]["content"].strip()
            
            # استخراج الـ JSON
            m = re.search(r'\{[\s\S]+\}', content)
            if m:
                return json.loads(m.group())
            return {"thought": "فشل الاستخراج", "tool_name": "", "arguments": {}}
    except Exception as e:
        logger.warning(f"  ⚠️ LLM error: {e}")
        return {"thought": f"خطأ: {e}", "tool_name": "", "arguments": {}}


def _db_inject_action(decision: str, action: Dict, result: Dict):
    """يحفظ ما قام بعمله كدليل في الذاكرة"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cur = conn.cursor()
        key = f"action_taken:{int(time.time())}"
        
        data = {
            "trigger_decision": decision,
            "action_planned": action,
            "action_result": result,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        
        cur.execute(
            "INSERT INTO beliefs (key, value, utility_score, updated_at) VALUES (?,?,?,?)",
            (key, json.dumps(data, ensure_ascii=False), 0.95, time.time())
        )
        conn.commit(); conn.close()
    except Exception as e:
        logger.error(f"  DB error: {e}")


class DecisionEngine:
    def __init__(self):
        # تعريف دقيق جداً للمتغيرات حتى لا يهلوِس النموذج بأسماء أخرى
        self.important_tools = [
            {"name": "execute_command", "desc": "تنفيذ أمر bash", "args": {"cmd": "str"}},
            {"name": "write_file", "desc": "كتابة محتوى لملف", "args": {"path": "str", "content": "str"}},
            {"name": "service_control", "desc": "إدارة خدمات النظام", "args": {"name": "str", "action": "start|stop|restart"}},
            {"name": "process_kill", "desc": "إنهاء عملية عبر PID", "args": {"pid": "int"}},
            {"name": "update_env_var", "desc": "تحديث متغير بيئة", "args": {"key": "str", "value": "str"}}
        ]
        logger.info("⚡ DecisionEngine initialized (Action Layer active)")

    def execute_decision(self, synthesis: Dict) -> Dict:
        """يأخذ التركيب الشامل وينفذ القرار"""
        decision_text = synthesis.get('key_decision', '')
        focus = synthesis.get('next_hour_focus', '')
        
        if not decision_text or "لا يوجد قرار مهم" in decision_text or "لا شيء" in decision_text:
            logger.info("  ⚖️ القرار: الاستمرار في الوضع الحالي (لا يوجد فعل مباشر)")
            return {"status": "no_action_needed"}

        logger.info("\n" + "─" * 55)
        logger.info(f"⚖️ [DECISION ENGINE] تنفيذ القرار...")
        logger.info(f"   القرار: {decision_text[:100]}")
        logger.info("─" * 55)

        # استدعاء LLM لتحديد الأداة
        prompt = f"""هذا هو القرار الاستراتيجي الذي خرجت به الدورة الحالية:
القرار: {decision_text}
التركيز: {focus}

السؤال: هل يوجد أداة واحدة يجب تشغيلها الآن فوراً لتنفيذ هذا القرار؟ (مثلاً كتابة سكريبت، إعادة تشغيل خدمة، تحديث إعدادات)
إذا نعم، اختر الأداة وأعطني المتغيرات. وإلا اترك tool_name فارغاً."""

        action_plan = _ask_brain_with_tools(prompt, self.important_tools)
        
        tool_name = action_plan.get("tool_name", "")
        args = action_plan.get("arguments", {})
        thought = action_plan.get("thought", "")

        logger.info(f"  💭 التفكير: {thought}")

        if not tool_name or tool_name.lower() == "none" or tool_name == "":
            logger.info("  ✋ النتيجة: القرار مجرد استنتاج/توجيه. لا يحتاج تنفيذ أداة تقنية حالياً.")
            return {"status": "skipped", "thought": thought}
        
        logger.info(f"  🛠️ تنفيذ الأداة: {tool_name} | {args}")
        
        # تنفيذ الأداة فعلياً
        start = time.time()
        result = use_tool(tool_name, **args)
        elapsed = round(time.time() - start, 2)
        
        success = result.get("success", False)
        
        if success:
            logger.info(f"  ✅ الأداة نجحت (في {elapsed}s).")
            # سجل التنفيذ الناجح في الذاكرة
            _db_inject_action(decision_text, action_plan, result)
        else:
            logger.warning(f"  ❌ الأداة فشلت: {result.get('error')}")

        return {"status": "executed", "action": action_plan, "result": result}
        
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser("Manual Decision Engine execution")
    parser.add_argument("--decision", type=str, required=True, help="القرار المباشر لتنفيذه")
    args = parser.parse_args()
    
    engine = DecisionEngine()
    engine.execute_decision({
        "key_decision": args.decision,
        "next_hour_focus": "تنفيذ فوري"
    })
