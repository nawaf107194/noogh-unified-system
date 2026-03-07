#!/usr/bin/env python3
"""
NOOGH Trajectory Recorder - RunPod Version
============================================
Runs DIRECTLY on the RunPod pod, connects to localhost:8000.
Saves results as JSONL, then download the file.

Usage (on RunPod terminal):
  python3 run_on_pod.py
"""

import json
import time
import random
import requests
from datetime import datetime

API_URL = "http://localhost:8000/v1/chat/completions"
MODEL = "noogh-teacher"
OUTPUT_FILE = "/workspace/NOOGH_TEACHER_TRAJECTORIES.jsonl"

SYSTEM_PROMPT = """أنت NOOGH، وكيل ذكاء اصطناعي سيادي (Sovereign AI Agent).
مهامك الأساسية:
1. تحليل الأنظمة والكود والبنية التحتية
2. حماية وتأمين النظام
3. تطوير وتحسين نفسك
4. إدارة الموارد (CPU, RAM, GPU, Disk)
5. التخطيط والتنفيذ الذاتي

أنت تعمل على نظام Ubuntu Linux مع GPU (NVIDIA).
تستخدم الأدوات التالية عند الحاجة:

الأدوات المتاحة:
- file.read(path): قراءة محتوى ملف
- file.write(path, content): كتابة ملف
- file.list(directory): سرد محتويات مجلد
- sys.exec(command): تنفيذ أمر في الطرفية
- sys.processes(): عرض العمليات الجارية
- sys.resources(): عرض حالة الموارد (CPU/RAM/Disk)
- gpu.status(): حالة GPU
- net.scan(target): فحص شبكة
- net.request(url, method): إرسال طلب HTTP
- sec.audit(target): تدقيق أمني
- sec.permissions(path): فحص صلاحيات
- code.analyze(path): تحليل كود
- code.refactor(path, changes): إعادة هيكلة كود
- mem.store(key, value): حفظ في الذاكرة
- mem.search(query): بحث في الذاكرة
- plan.create(goal, steps): إنشاء خطة
- plan.execute(plan_id): تنفيذ خطة
- self.analyze(): تحليل ذاتي
- self.improve(target): تحسين ذاتي

عند الرد:
1. فكّر خطوة بخطوة
2. استخدم الأدوات عند الحاجة (بصيغة JSON)
3. اشرح أسبابك
4. قدم نتائج واضحة
"""

# === All Tasks ===
TASKS = [
    # System Analysis
    ("system_analysis", "حلل ملف neural_engine/model_authority.py واذكر: 1) الغرض منه 2) المشاكل المحتملة 3) اقتراحات التحسين"),
    ("system_analysis", "حلل ملف unified_core/agent_daemon.py واذكر: 1) الغرض منه 2) المشاكل المحتملة 3) اقتراحات التحسين"),
    ("system_analysis", "حلل ملف neural_engine/react_loop.py واذكر: 1) الغرض منه 2) المشاكل المحتملة 3) اقتراحات التحسين"),
    ("system_analysis", "حلل ملف gateway/app/main.py واذكر: 1) الغرض منه 2) المشاكل المحتملة 3) اقتراحات التحسين"),
    ("system_analysis", "حلل ملف neural_engine/api/routes.py واذكر: 1) الغرض منه 2) المشاكل المحتملة 3) اقتراحات التحسين"),
    ("system_analysis", "اعمل تحليل شامل لمجلد neural_engine/ واشرح بنيته المعمارية"),
    ("system_analysis", "اعمل تحليل شامل لمجلد unified_core/ واشرح بنيته المعمارية"),
    ("system_analysis", "اعمل تحليل شامل لمجلد gateway/ واشرح بنيته المعمارية"),
    
    # Security
    ("security", "افحص أمان ملف neural_engine/api/routes.py وابحث عن ثغرات أمنية محتملة"),
    ("security", "افحص أمان ملف gateway/app/api/routes.py وابحث عن ثغرات أمنية محتملة"),
    ("security", "افحص أمان ملف neural_engine/tools/tool_executor.py وابحث عن ثغرات أمنية محتملة"),
    ("security", "نفذ تدقيق أمني شامل للنظام: افحص البورتات المفتوحة، الصلاحيات، الخدمات المعرضة"),
    ("security", "حلل مخاطر SQL Injection في كل الملفات التي تتعامل مع قواعد البيانات"),
    ("security", "افحص إعدادات SSH وsudo وتأكد من تطبيق مبدأ الحد الأدنى من الصلاحيات"),
    ("security", "ابحث عن كلمات مرور أو API keys مكشوفة في الكود المصدري"),
    
    # Planning
    ("planning", "خطط لترقية نظام الذاكرة إلى Redis Cluster مع الحفاظ على التوافقية"),
    ("planning", "خطط لترقية Neural Engine لدعم multiple models مع الحفاظ على التوافقية"),
    ("planning", "خطط لترقية نظام الحوكمة ليشمل multi-level approval مع الحفاظ على التوافقية"),
    ("planning", "خطط لترقية Dashboard لتشمل real-time monitoring مع الحفاظ على التوافقية"),
    ("planning", "ضع خطة لتدريب نموذج LoRA جديد مع تحسين جودة البيانات"),
    ("planning", "صمم استراتيجية للنسخ الاحتياطي التلقائي وخطة التعافي من الكوارث"),
    
    # Code Writing
    ("code_writing", "اكتب HealthCheck service يراقب كل خدمات النظام كل 30 ثانية"),
    ("code_writing", "اكتب Backup script يحفظ نسخة احتياطية من الداتابيس والتكوينات"),
    ("code_writing", "اكتب Log analyzer يكتشف الأنماط المتكررة في الأخطاء"),
    ("code_writing", "اكتب Resource monitor ينبه لما GPU أو RAM يوصل 90%"),
    ("code_writing", "اكتب Auto-restart service يعيد تشغيل الخدمات اللي تطيح"),
    ("code_writing", "اكتب API rate limiter يحمي endpoints من الاستخدام المفرط"),
    ("code_writing", "اكتب Configuration validator يتحقق من صحة كل ملفات .env و config"),
    ("code_writing", "اكتب Memory leak detector يراقب استهلاك الذاكرة وينبه عند التسرب"),
    
    # Error Recovery
    ("error_recovery", "الخدمة Neural Engine طاحت بهالخطأ: ConnectionRefusedError: [Errno 111] Connection refused. حلل وأصلح."),
    ("error_recovery", "الخدمة Gateway طاحت بهالخطأ: CUDA out of memory. Tried to allocate 2.00 GiB. حلل وأصلح."),
    ("error_recovery", "الخدمة Agent Daemon طاحت بهالخطأ: sqlite3.OperationalError: database is locked. حلل وأصلح."),
    ("error_recovery", "الخدمة Redis طاحت بهالخطأ: ImportError: cannot import name 'ReasoningEngine'. حلل وأصلح."),
    ("error_recovery", "الخدمة Neural Engine طاحت بهالخطأ: TimeoutError: Task exceeded 30s limit. حلل وأصلح."),
    ("error_recovery", "النظام يعاني من بطء شديد بعد تحديث GPU driver. حلل المشكلة وأصلحها."),
    ("error_recovery", "ملف الكونفيق تالف ولا يقدر النظام يقرأه. كيف تستعيد الإعدادات؟"),
    
    # Self Improvement
    ("self_improvement", "حلل أداءك الحالي واقترح 3 تحسينات يمكنك تنفيذها الآن"),
    ("self_improvement", "راجع كودك في neural_engine/react_loop.py واكتب نسخة محسنة"),
    ("self_improvement", "راجع كودك في neural_engine/cognitive_trace.py واكتب نسخة محسنة"),
    ("self_improvement", "كيف يمكنك تحسين قدرتك على التعلم من الأخطاء السابقة؟ اشرح بالتفصيل مع أمثلة كود"),
    ("self_improvement", "صمم نظام 'ذاكرة طويلة المدى' يسمح لك بتذكر الأنماط المتكررة"),
    
    # Ubuntu Administration
    ("ubuntu_admin", "اعمل فحص شامل للنظام: مساحة القرص، استهلاك RAM، الخدمات الشغالة"),
    ("ubuntu_admin", "أنشئ systemd service جديدة لـ NOOGH مع auto-restart وlog rotation"),
    ("ubuntu_admin", "حسّن أداء النظام: اضبط swappiness، disk scheduler، network buffers"),
    ("ubuntu_admin", "اعمل firewall rules تسمح فقط ببورتات النظام المطلوبة"),
    ("ubuntu_admin", "أنشئ cron job للنسخ الاحتياطي اليومي الساعة 3 الفجر"),
    ("ubuntu_admin", "اعمل script لمراقبة مساحة القرص وتنبيه لما تنزل عن 10%"),
    ("ubuntu_admin", "اضبط logrotate لكل ملفات لوق النظام"),
    
    # Complex Tasks
    ("complex_task", "نفذ المهمة التالية خطوة بخطوة مع استخدام الأدوات: اكتشف أي ملفات في المشروع أكبر من 10MB واقترح حلول لتقليل حجمها"),
    ("complex_task", "نفذ المهمة التالية خطوة بخطوة مع استخدام الأدوات: حلل كل ملفات Python في neural_engine/ واكتب تقرير عن جودة الكود"),
    ("complex_task", "نفذ المهمة التالية خطوة بخطوة مع استخدام الأدوات: ابحث عن أي أسرار مكشوفة (API keys, passwords) في الكود وقدم تقرير"),
    ("complex_task", "نفذ المهمة التالية خطوة بخطوة مع استخدام الأدوات: اعمل profiling للنظام واكتشف أكبر 5 bottlenecks"),
    ("complex_task", "نفذ المهمة التالية خطوة بخطوة مع استخدام الأدوات: صمم وحدة اختبار شاملة لـ model_authority.py"),
    ("complex_task", "نفذ المهمة التالية خطوة بخطوة: صمم نظام مراقبة ذكي يكتشف الأنماط غير الطبيعية في سلوك النظام"),
    ("complex_task", "صمم واجهة API كاملة لإدارة الوكلاء الذكيين مع CRUD operations وauthentication"),
    
    # Governance & Decision Making
    ("governance", "صمم نظام حوكمة يقرر متى يسمح بتعديل ملفات النظام الحساسة ومتى يمنع"),
    ("governance", "كيف تتعامل مع تعارض بين هدفين: تحسين الأداء مقابل الحفاظ على الاستقرار؟"),
    ("governance", "صمم نظام أذونات متعدد المستويات للوكيل الذكي: ماذا يقدر يسوي بدون إذن وماذا يحتاج موافقة"),
    
    # Multi-turn Conversations
    ("multi_turn", "أنت تراقب النظام ولاحظت ارتفاع في استهلاك CPU لـ 95%. ابدأ بالتحقيق خطوة بخطوة: 1) اعرض العمليات 2) حدد السبب 3) اتخذ إجراء"),
    ("multi_turn", "المستخدم طلب إضافة ميزة جديدة: نظام تنبيهات عبر Telegram. خطط للتنفيذ من البداية للنهاية"),
    ("multi_turn", "اكتشفت محاولة اختراق على البورت 22. ماذا تفعل؟ نفذ الخطوات كاملة"),
]


def score_response(response, category):
    """Auto-score response quality (0.0 - 1.0)."""
    score = 0.0
    if len(response) > 200: score += 0.2
    if len(response) > 500: score += 0.1
    if len(response) > 1000: score += 0.1
    
    tool_indicators = ["file.read", "sys.exec", "sec.audit", "code.analyze",
                       "net.scan", "gpu.status", "mem.search", "plan.create"]
    tool_count = sum(1 for t in tool_indicators if t in response)
    if tool_count >= 1: score += 0.15
    if tool_count >= 2: score += 0.1
    
    if any(f"{i}." in response or f"{i})" in response for i in range(1, 6)):
        score += 0.1
    
    arabic_chars = sum(1 for c in response if '\u0600' <= c <= '\u06FF')
    if arabic_chars > 50: score += 0.1
    
    tech_terms = ["API", "GPU", "VRAM", "CPU", "RAM", "systemd", "docker",
                  "LoRA", "model", "endpoint", "token", "database"]
    tech_count = sum(1 for t in tech_terms if t.lower() in response.lower())
    if tech_count >= 3: score += 0.15
    
    return min(score, 1.0)


def call_teacher(messages, max_tokens=2048):
    """Call the teacher model."""
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": max_tokens,
    }
    
    start = time.time()
    try:
        r = requests.post(API_URL, json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()
        latency = int((time.time() - start) * 1000)
        
        return {
            "content": data["choices"][0]["message"]["content"],
            "input_tokens": data.get("usage", {}).get("prompt_tokens", 0),
            "output_tokens": data.get("usage", {}).get("completion_tokens", 0),
            "latency_ms": latency,
            "success": True,
        }
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return {"content": "", "success": False, "error": str(e)}


def main():
    print("=" * 60)
    print("🎓 NOOGH Teacher Trajectory Recorder")
    print(f"   Model: {MODEL}")
    print(f"   Tasks: {len(TASKS)}")
    print(f"   Output: {OUTPUT_FILE}")
    print("=" * 60)
    
    # Health check
    try:
        r = requests.get("http://localhost:8000/v1/models", timeout=5)
        print(f"✅ Teacher API healthy: {r.status_code}")
    except:
        print("❌ Teacher API not reachable!")
        return
    
    random.shuffle(TASKS)
    
    successful = 0
    total_tokens = 0
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for i, (category, task) in enumerate(TASKS):
            print(f"\n{'─' * 50}")
            print(f"📋 [{i+1}/{len(TASKS)}] {category}")
            print(f"   {task[:80]}...")
            
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": task}
            ]
            
            result = call_teacher(messages)
            
            if result["success"]:
                quality = score_response(result["content"], category)
                
                # Write JSONL line
                entry = {
                    "messages": messages + [{"role": "assistant", "content": result["content"]}],
                    "category": category,
                    "quality": quality,
                    "input_tokens": result["input_tokens"],
                    "output_tokens": result["output_tokens"],
                    "latency_ms": result["latency_ms"],
                    "timestamp": datetime.now().isoformat(),
                }
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                f.flush()
                
                successful += 1
                total_tokens += result["output_tokens"]
                print(f"   ✅ Quality: {quality:.2f} | Tokens: {result['output_tokens']} | {result['latency_ms']}ms")
            else:
                print(f"   ❌ Failed: {result.get('error', 'Unknown')}")
            
            time.sleep(0.5)
    
    print(f"\n{'=' * 60}")
    print(f"📊 Session Complete!")
    print(f"   ✅ Successful: {successful}/{len(TASKS)}")
    print(f"   📝 Total tokens: {total_tokens:,}")
    print(f"   📦 Output: {OUTPUT_FILE}")
    print(f"   💡 Download this file to your local machine!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
