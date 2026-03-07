#!/usr/bin/env python3
"""
NOOGH Strategic Goals Supervisor
------------------------------------------------------
يدير الأهداف الاستراتيجية قصيرة وطويلة الأمد لنظام NOOGH.
يعمل كـ "بوصلة" توجه المنسق (Orchestrator) نحو الغاية الكبرى
وتمنعه من الضياع في المشاكل الجزئية.
"""

import sys, os, json, time, sqlite3, logging
from typing import Dict, List, Any

sys.path.insert(0, "/home/noogh/projects/noogh_unified_system/src")
from unified_core.brain_tools import db_inject_belief

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | strategy | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/home/noogh/projects/noogh_unified_system/src/logs/strategic_goals.log")
    ]
)
logger = logging.getLogger("strategy")

SRC = "/home/noogh/projects/noogh_unified_system/src"
DB_PATH = f"{SRC}/data/shared_memory.sqlite"
VLLM_URL = os.environ.get("NEURAL_ENGINE_URL", "http://localhost:11434")
MODEL = os.environ.get("VLLM_MODEL_NAME", "qwen2.5-coder:7b")


class StrategicGoalsSupervisor:
    """المشرف الاستراتيجي: يحتفظ بالأهداف، يقيمها، ويولد أهدافاً جديدة"""
    
    def __init__(self):
        self._ensure_initial_goals_exist()
        logger.info("🧭 Strategic Goals Supervisor initialized")

    def _ensure_initial_goals_exist(self):
        """يحقن الأهداف الابتدائية في الذاكرة إذا لم تكن موجودة"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()
            cur.execute("SELECT value FROM beliefs WHERE key='system:strategic_goals'")
            row = cur.fetchone()
            
            if not row:
                logger.info("  🌱 Injection initial strategic goals into memory.")
                initial_path = f"{SRC}/data/initial_goals.json"
                if os.path.exists(initial_path):
                    with open(initial_path, "r", encoding="utf-8") as f:
                        goals = json.load(f)
                else:
                    goals = {
                        "long_term": [
                            "الوصول إلى استقلالية كاملة في صيانة وإصلاح الكود (Self-Healing)",
                            "بناء نماذج معرفية لكيفية تحسين بنية الـ Agent بشكل مستمر"
                        ],
                        "short_term": [
                            "حل مشكلات استهلاك الذاكرة في العمليات الحالية",
                            "تنظيف الذاكرة (Beliefs) من الأفكار ذات الجودة المنخفضة"
                        ]
                    }
                    
                cur.execute(
                    "INSERT INTO beliefs (key,value,utility_score,updated_at) VALUES (?,?,?,?)",
                    ("system:strategic_goals", json.dumps(goals, ensure_ascii=False), 0.99, time.time())
                )
                conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"  ❌ DB Error in initial goals: {e}")

    def get_current_goals(self) -> Dict:
        """يسترجع الأهداف الحالية من الذاكرة"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()
            cur.execute("SELECT value FROM beliefs WHERE key='system:strategic_goals'")
            row = cur.fetchone()
            conn.close()
            if row:
                return json.loads(row[0])
            return {"short_term": [], "long_term": []}
        except Exception:
            return {"short_term": [], "long_term": []}

    def _ask_brain_strategy(self, prompt: str) -> Dict:
        """يطلب من الدماغ تقييم أهدافه لتوليد أهداف جديدة"""
        import urllib.request
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "أنت المخطط الاستراتيجي (Strategic Planner) لـ NOOGH. مهمتك تحديث الأهداف طويلة وقصيرة الأمد بناءً على حالة النظام ومسار تطوره. أجب بصيغة JSON حصراً تتضمن 'long_term' و 'short_term'."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.4,
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
                import re
                m = re.search(r'\{[\s\S]+\}', content)
                if m:
                    return json.loads(m.group())
        except Exception as e:
            logger.warning(f"  ⚠️ LLM Strategy Error: {e}")
        return {}

    def review_and_update_goals(self, synthesis: Dict, system_state: Dict) -> Dict:
        """
        يراجع المنجزات (ما حدث في آخر ساعة) وحالة النظام الحالية،
        ويحدث الأهداف (قد يحث بعضها ويضيف جديد).
        """
        logger.info("\n" + "─" * 55)
        logger.info("🧭 [STRATEGIC SUPERVISOR] مراجعة وتحديث الأهداف...")
        logger.info("─" * 55)
        
        current_goals = self.get_current_goals()
        
        prompt = f"""هذه الأهداف الاستراتيجية الحالية لنظام NOOGH:
أهداف طويلة الأمد: {current_goals.get('long_term', [])}
أهداف قصيرة الأمد: {current_goals.get('short_term', [])}

هذا ما تم إنجازه ولاحظته الدورة الحالية (Synthesis):
{json.dumps(synthesis, ensure_ascii=False)}

وهذه حالة النظام الصحية (System State):
الصحة: {system_state.get('health', 'Unknown')}
المشاكل: {system_state.get('main_issues', 'None')}

مهمتك:
1. إزالة الأهداف قصيرة الأمد التي تم تحقيقها أو لم تعد مهمة.
2. إضافة هدف قصير أمد جديد واحد بناءً على المشاكل الحالية في System State إن وجدت.
3. الإبقاء على أو تحسين الأهداف طويلة الأمد للمرحلة القادمة.

أخرج لي فقط كائن JSON بتنسيق:
{{
  "long_term": ["الهدف1", "الهدف2"],
  "short_term": ["الهدف_القصير1", "الهدف_القصير2"],
  "reflection": "ما هو تقييمك لمسار التقدم ككل"
}}"""

        new_strategy = self._ask_brain_strategy(prompt)
        
        if new_strategy and "short_term" in new_strategy and "long_term" in new_strategy:
            reflection = new_strategy.get("reflection", "")
            logger.info(f"  💭 تقييم المسار: {reflection}")
            logger.info(f"  🎯 أهداف المدى القصير الآن: {new_strategy['short_term']}")
            
            # تحديث الذاكرة
            db_inject_belief("system:strategic_goals", {
                "long_term": new_strategy["long_term"],
                "short_term": new_strategy["short_term"],
                "updated_at": datetime.now().isoformat() if 'datetime' in globals() else time.strftime("%Y-%m-%dT%H:%M:%S")
            }, utility=0.99)
            
            return new_strategy

        logger.info("  ℹ️ بقيت الأهداف على حالها.")
        return current_goals
