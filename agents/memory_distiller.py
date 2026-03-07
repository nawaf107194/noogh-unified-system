#!/usr/bin/env python3
"""
NOOGH Memory Distiller — مصفِّاة الذاكرة المركزية
------------------------------------------------------
يمنع اختناق قاعدة البيانات وانهيار الأداء عن طريق:
1. اضمحلال (Decay) أهمية المعلومات مع مرور الزمن.
2. حذف المعتقدات عديمة النفع (Utility < 0.3).
3. دمج المعتقدات المتشابهة لتوفير مساحة وتكوين وعي أعمق.
"""

import sys, os, json, time, sqlite3, logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

sys.path.insert(0, "/home/noogh/projects/noogh_unified_system/src")
from unified_core.brain_tools import db_inject_belief

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | memory | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/home/noogh/projects/noogh_unified_system/src/logs/memory_distiller.log")
    ]
)
logger = logging.getLogger("memory")

SRC = "/home/noogh/projects/noogh_unified_system/src"
DB_PATH = f"{SRC}/data/shared_memory.sqlite"
VLLM_URL = os.environ.get("NEURAL_ENGINE_URL", "http://localhost:11434")
MODEL = os.environ.get("VLLM_MODEL_NAME", "qwen2.5-coder:7b")


class MemoryDistiller:
    def __init__(self):
        logger.info("🧠 Memory Distiller initialized")

    def _execute_query(self, query: str, params: tuple = ()) -> List[Tuple]:
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            cur = conn.cursor()
            cur.execute(query, params)
            if query.strip().upper().startswith("SELECT"):
                result = cur.fetchall()
            else:
                conn.commit()
                result = [(cur.rowcount,)]
            conn.close()
            return result
        except Exception as e:
            logger.error(f"  ❌ DB Error: {e}")
            return []

    def decay_old_beliefs(self, decay_rate: float = 0.05, older_than_days: int = 1):
        """يقلل من قيمة الـ Utility للمعتقدات القديمة التي لم يتم تحديثها"""
        logger.info(f"  ⏳ Decaying beliefs older than {older_than_days} days by {decay_rate}...")
        cutoff_time = time.time() - (older_than_days * 86400)
        
        # لا تضمحل المعتقدات الاستراتيجية
        query = """
            UPDATE beliefs 
            SET utility_score = MAX(0.1, utility_score - ?)
            WHERE updated_at < ? AND key NOT LIKE 'system:%'
        """
        res = self._execute_query(query, (decay_rate, cutoff_time))
        if res:
            logger.info(f"    ✔️ Decayed {res[0][0]} old beliefs.")

    def purge_low_utility(self, threshold: float = 0.3):
        """يحذف الأفكار التي أصبحت غير مفيدة إطلاقاً"""
        logger.info(f"  🗑️ Purging beliefs with utility < {threshold}...")
        query = "DELETE FROM beliefs WHERE utility_score < ? AND key NOT LIKE 'system:%'"
        res = self._execute_query(query, (threshold,))
        if res:
            deleted_count = res[0][0]
            if deleted_count > 0:
                logger.info(f"    ✔️ Purged {deleted_count} low-utility beliefs.")

    def _ask_brain_to_merge(self, topic: str, beliefs: List[Dict]) -> Dict:
        """يطلب من الدماغ دمج مجموعة معتقدات متشابهة في قاعدة واحدة صلبة"""
        import urllib.request
        
        beliefs_str = json.dumps(beliefs, ensure_ascii=False, indent=2)
        
        prompt = f"""أنت NOOGH، مسئول دمج الذاكرة. 
لديك مجموعة من المعتقدات المتناثرة حول موضوع '{topic}'. بعضها قديم وبعضها متكرر.
قم بقراءتها، استخلص الخلاصة العميقة الموحدة، واكتبها كمعتقد واحد ذو قيمة عالية.

المعتقدات القديمة:
{beliefs_str}

قاعدة: أخرج النتيجة فقط كـ JSON بالتنسيق التالي:
{{
  "merged_concept": "خلاصة المعرفة العميقة المدمجة",
  "utility": 0.90,
  "rationale": "لماذا هذا الاستنتاج أفضل وأشمل"
}}"""

        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "أنت نظام دمج الذاكرة الدلالية. أجب بصيغة JSON حصراً."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.2,
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
            logger.warning(f"  ⚠️ LLM Merge Error: {e}")
        return {}

    def merge_redundant_beliefs(self):
        """يبحث عن المعتقدات من نفس الفئة (مثلاً agent_understanding) ويدمجها"""
        logger.info("  🧩 Merging fragmented beliefs...")
        
        # استخراج أنواع المفاتيح الشائعة التي تتكرر
        query_categories = """
            SELECT substr(key, 1, instr(key, ':') - 1) as category, COUNT(*) as cnt
            FROM beliefs
            WHERE key LIKE '%:%' AND key NOT LIKE 'system:%'
            GROUP BY category
            HAVING cnt > 5
        """
        categories = self._execute_query(query_categories)
        
        total_merged = 0
        for category, count in categories:
            logger.info(f"    🔍 Analyzing category '{category}' ({count} entries)")
            
            # جلب أقدم 5 معتقدات من نفس الفئة لدمجها
            items_query = """
                SELECT key, value, utility_score 
                FROM beliefs 
                WHERE key LIKE ? 
                ORDER BY updated_at ASC LIMIT 5
            """
            rows = self._execute_query(items_query, (f"{category}:%",))
            if not rows or len(rows) < 2:
                continue
                
            beliefs_to_merge = [{"key": r[0], "value": r[1][:250], "u": r[2]} for r in rows]
            keys_to_delete = [r[0] for r in rows]
            
            merge_result = self._ask_brain_to_merge(category, beliefs_to_merge)
            
            if merge_result and "merged_concept" in merge_result:
                new_key = f"synthesized:{category}:{int(time.time())}"
                new_utility = min(0.98, merge_result.get("utility", 0.90))
                
                # حذف القديم
                placeholders = ','.join(['?'] * len(keys_to_delete))
                self._execute_query(f"DELETE FROM beliefs WHERE key IN ({placeholders})", tuple(keys_to_delete))
                
                # حقن الجديد
                db_inject_belief(new_key, {
                    "summary": merge_result["merged_concept"],
                    "rationale": merge_result.get("rationale", ""),
                    "merged_from_count": len(keys_to_delete)
                }, utility=new_utility)
                
                logger.info(f"    🧬 Merged {len(keys_to_delete)} items into -> {new_key[:40]}")
                total_merged += len(keys_to_delete)
                
        if total_merged > 0:
            logger.info(f"  ✅ Successfully compressed {total_merged} fragmented beliefs.")
        else:
            logger.info("  ℹ️ No redundant fragmented beliefs needed merging.")

    def run_distillation_cycle(self) -> Dict:
        """تشغيل دورة تقطير وتنظيف كاملة"""
        logger.info("\n" + "─" * 55)
        logger.info("⚗️ [MEMORY DISTILLER] دورة تنظيف وتقطير الذاكرة...")
        logger.info("─" * 55)
        
        start_time = time.time()
        
        # 1. إضعاف القديم
        self.decay_old_beliefs()
        
        # 2. حذف الميت
        self.purge_low_utility()
        
        # 3. دمج المتناثر
        self.merge_redundant_beliefs()
        
        elapsed = round(time.time() - start_time, 2)
        logger.info(f"✅ Memory Distillation completed in {elapsed}s.")
        
        return {"status": "success", "elapsed": elapsed}

if __name__ == "__main__":
    distiller = MemoryDistiller()
    distiller.run_distillation_cycle()
