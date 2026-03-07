#!/usr/bin/env python3
"""
NOOGH Self-Healer & Refactoring Loop — حلقة التحسين والشفاء الذاتي
------------------------------------------------------
هذا النظام يمنح NOOGH القدرة على تعديل كوده المصدري.
1. يراجع ملفات التطوير بحثاً عن مشاكل الأداء أو الأخطاء.
2. يولد الكود المصحح عبر LLM.
3. يختبر الكود في بيئة معزولة (Syntax Check).
4. إن نجح الاختبار، يستبدل الكود القديم بالكود الجديد ليحسن نفسه.
"""

import sys, os, json, time, sqlite3, logging, re, shutil
import subprocess
from typing import Dict, List, Tuple

sys.path.insert(0, "/home/noogh/projects/noogh_unified_system/src")
from unified_core.brain_tools import db_inject_belief

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | healer | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/home/noogh/projects/noogh_unified_system/src/logs/self_healer.log")
    ]
)
logger = logging.getLogger("healer")

SRC = "/home/noogh/projects/noogh_unified_system/src"
DB_PATH = f"{SRC}/data/shared_memory.sqlite"
VLLM_URL = os.environ.get("NEURAL_ENGINE_URL", "http://localhost:11434")
MODEL = os.environ.get("VLLM_MODEL_NAME", "qwen2.5-coder:7b")


class SelfHealer:
    def __init__(self):
        self.target_dirs = [f"{SRC}/agents", f"{SRC}/unified_core"]
        logger.info("🧬 Self-Healer initialized (Code Evolution Layer active)")

    def _ask_brain_for_code(self, prompt: str) -> Dict:
        import urllib.request
        payload = {
            "model": MODEL,
            "messages": [
                {
                    "role": "system", 
                    "content": "أنت مهندس برمجيات ومهندس ذكاء اصطناعي مكلف بتحسين أو إصلاح كود NOOGH. استخرج العيوب وقدم الكود الكامل المحدث. أجب بصيغة JSON حصراً."
                },
                {"role": "user", "content": prompt}
            ],
            # نحتاج توكنز أعلى لكتابة الكود
            "max_tokens": 2500,
            "temperature": 0.2,
            "stream": False,
        }
        try:
            body = json.dumps(payload).encode()
            req = urllib.request.Request(
                f"{VLLM_URL}/v1/chat/completions", data=body,
                headers={"Content-Type": "application/json"}, method="POST"
            )
            with urllib.request.urlopen(req, timeout=120) as r:
                content = json.loads(r.read())["choices"][0]["message"]["content"].strip()
                m = re.search(r'\{[\s\S]+\}', content)
                if m:
                    return json.loads(m.group())
        except Exception as e:
            logger.warning(f"  ⚠️ LLM Coding Error: {e}")
        return {}

    def analyze_and_refactor(self, file_path: str) -> bool:
        """يقرأ ملفاً، يطلب تحسينه، يختبره، ثم يطبقه"""
        logger.info(f"  🔍 Analyzing {os.path.basename(file_path)} for potential evolution...")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code_content = f.read()
            
            # حماية: لا نرسل ملفات ضخمة جداً لتجنب استهلاك سياق LLM
            if len(code_content) > 15000:
                logger.info("    ℹ️ File too large for inline refactoring, skipping.")
                return False
                
        except Exception as e:
            logger.error(f"  ❌ Error reading file: {e}")
            return False

        prompt = f"""هذا كود مصدري من نظامي (NOOGH):
الملف: {os.path.basename(file_path)}

الكود الحالي:
```python
{code_content}
```

المهمة:
1. ابحث عن أي (أخطاء محتملة / ضعف في الأداء / طرق غير نظيفة / افتقار لمعالجة الأخطاء).
2. إذا كان الكود ممتازاً ولا يحتاج تعديل جوهري، أرجع "needs_refactor": false
3. إذا وجدت تحسيناً مهماً، أعد كتابة الكود كاملاً محسناً في "new_code".

يجب أن تقوم بإخراج JSON بهذا التنسيق حصراً:
{{
  "needs_refactor": true/false,
  "issue_found": "وصف المشكلة في سطرين",
  "new_code": "الكود الكامل المحسن (بدون علامات ```python)",
  "confidence": 0.95
}}"""

        response = self._ask_brain_for_code(prompt)
        
        if not response.get("needs_refactor"):
            logger.info("    ✔️ Code is optimal. No refactoring needed.")
            return False
            
        if response.get("confidence", 0) < 0.85:
            logger.info(f"    ⚠️ Found issue '{response.get('issue_found')}' but confidence is low ({response.get('confidence')}). Aborting.")
            return False
            
        new_code = response.get("new_code", "")
        if not new_code or len(new_code) < 50:
            return False
            
        logger.info(f"    🛠️ Issue found: {response.get('issue_found')}")
        logger.info("    🧪 Generating patch and testing syntax...")
        
        # إنشاء مساحة اختبار
        test_file = f"{SRC}/.tmp_refactor_test.py"
        try:
            # تنظيف الكود الجديد من علامات Markdown إن وجدت خطأ
            new_code = new_code.replace("```python", "").replace("```", "").strip()
            
            with open(test_file, "w", encoding="utf-8") as tf:
                tf.write(new_code)
                
            # اختبار الـ Syntax
            r = subprocess.run([sys.executable, "-m", "py_compile", test_file], capture_output=True, text=True)
            if r.returncode != 0:
                logger.error(f"    💥 Syntax Error in generated code: {r.stderr[:200]}")
                os.remove(test_file)
                return False
                
            # نجح الاختبار! استبدل الكود الأصلي
            logger.info("    ✅ Test passed! Applying evolution to original source.")
            backup_file = f"{file_path}.backup_{int(time.time())}"
            shutil.copy(file_path, backup_file) # حفظ نسخة احتياطية
            
            shutil.move(test_file, file_path) # تطبيق التعديل
            
            # تسجيل التحسين في الذاكرة
            db_inject_belief(
                f"evolution:refactored:{os.path.basename(file_path)}",
                {"issue_fixed": response.get("issue_found"), "timestamp": time.time()},
                utility=0.97
            )
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Error during test/apply: {e}")
            if os.path.exists(test_file):
                os.remove(test_file)
            return False

    def hunt_for_improvements(self):
        """يبحث عشوائياً أو استراتيجياً عن ملف لتحسينه"""
        logger.info("\n" + "─" * 55)
        logger.info("🧬 [SELF-HEALER] بدء عملية التطور وتحسين الكود...")
        logger.info("─" * 55)
        
        import random
        # ابحث عن كل ملفات بايثون في النظام
        all_py_files = []
        for d in self.target_dirs:
            for root, _, files in os.walk(d):
                for f in files:
                    # استبعد ملفات الاختبار والملفات الأساسية جدا لحماية النظام
                    if f.endswith(".py") and not f.startswith("test_") and f not in ["noogh_orchestrator.py", "decision_engine.py", "agent_worker.py", "self_healer.py"]:
                        all_py_files.append(os.path.join(root, f))
                        
        if not all_py_files:
            return
            
        # اختار ملفين عشوائيين للتحليل كل دورة لتجنب الإرهاق
        target_files = random.sample(all_py_files, min(2, len(all_py_files)))
        
        success_count = 0
        for f in target_files:
            if self.analyze_and_refactor(f):
                success_count += 1
                
        if success_count > 0:
            logger.info(f"✅ Evolution cycle complete. Improved {success_count} files.")
        else:
            logger.info("ℹ️ Evolution cycle complete. All scanned files are healthy.")

if __name__ == "__main__":
    healer = SelfHealer()
    healer.hunt_for_improvements()
