#!/usr/bin/env python3
"""
NOOGH Trajectory Recorder
==========================
Records every step from the Teacher model (72B) into a local SQLite database.
These trajectories are later used to train the Student model (7B).

Architecture:
  Local Machine → RunPod API (72B) → Record response → SQLite
"""

import json
import logging
import os
import sqlite3
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger(__name__)

# ─── Configuration ────────────────────────────────────────────

DB_PATH = Path(os.getenv(
    "NOOGH_TRAJECTORY_DB",
    "/home/noogh/projects/noogh_unified_system/src/data/trajectories.db"
))

TEACHER_API_URL = os.getenv("NOOGH_TEACHER_URL", "")  # Set to RunPod URL
TEACHER_API_KEY = os.getenv("NOOGH_TEACHER_KEY", "EMPTY")
TEACHER_MODEL = os.getenv("NOOGH_TEACHER_MODEL", "noogh-teacher")

# NOOGH System Prompt
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

# ─── Task Templates ───────────────────────────────────────────

TASK_TEMPLATES = [
    # === System Analysis ===
    {
        "category": "system_analysis",
        "task": "حلل ملف {file_path} واذكر: 1) الغرض منه 2) المشاكل المحتملة 3) اقتراحات التحسين",
        "variables": {"file_path": [
            "neural_engine/model_authority.py",
            "unified_core/agent_daemon.py",
            "neural_engine/react_loop.py",
            "gateway/app/main.py",
            "neural_engine/api/routes.py",
        ]}
    },
    {
        "category": "system_analysis",
        "task": "اعمل تحليل شامل لمجلد {directory} واشرح بنيته المعمارية",
        "variables": {"directory": [
            "neural_engine/",
            "unified_core/",
            "gateway/",
        ]}
    },
    # === Security ===
    {
        "category": "security",
        "task": "افحص أمان ملف {file_path} وابحث عن ثغرات أمنية محتملة",
        "variables": {"file_path": [
            "neural_engine/api/routes.py",
            "gateway/app/api/routes.py",
            "neural_engine/tools/tool_executor.py",
        ]}
    },
    {
        "category": "security",
        "task": "نفذ تدقيق أمني شامل للنظام: افحص البورتات المفتوحة، الصلاحيات، الخدمات المعرضة",
    },
    # === Planning ===
    {
        "category": "planning",
        "task": "خطط لترقية {component} مع الحفاظ على التوافقية",
        "variables": {"component": [
            "نظام الذاكرة إلى Redis Cluster",
            "Neural Engine لدعم multiple models",
            "نظام الحوكمة ليشمل multi-level approval",
            "Dashboard لتشمل real-time monitoring",
        ]}
    },
    # === Code Writing ===
    {
        "category": "code_writing",
        "task": "اكتب {component_desc}",
        "variables": {"component_desc": [
            "HealthCheck service يراقب كل خدمات النظام كل 30 ثانية",
            "Backup script يحفظ نسخة احتياطية من الداتابيس والتكوينات",
            "Log analyzer يكتشف الأنماط المتكررة في الأخطاء",
            "Resource monitor ينبه لما GPU أو RAM يوصل 90%",
            "Auto-restart service يعيد تشغيل الخدمات اللي تطيح",
        ]}
    },
    # === Error Recovery ===
    {
        "category": "error_recovery",
        "task": "الخدمة {service} طاحت بهالخطأ: {error}. حلل وأصلح.",
        "variables": {
            "service": ["Neural Engine", "Gateway", "Agent Daemon", "Redis"],
            "error": [
                "ConnectionRefusedError: [Errno 111] Connection refused",
                "CUDA out of memory. Tried to allocate 2.00 GiB",
                "sqlite3.OperationalError: database is locked",
                "ImportError: cannot import name 'ReasoningEngine'",
                "TimeoutError: Task exceeded 30s limit",
            ]
        }
    },
    # === Self Improvement ===
    {
        "category": "self_improvement",
        "task": "حلل أداءك الحالي واقترح 3 تحسينات يمكنك تنفيذها الآن",
    },
    {
        "category": "self_improvement",
        "task": "راجع كودك في {file_path} واكتب نسخة محسنة",
        "variables": {"file_path": [
            "neural_engine/react_loop.py",
            "neural_engine/cognitive_trace.py",
        ]}
    },
    # === Ubuntu Administration ===
    {
        "category": "ubuntu_admin",
        "task": "{admin_task}",
        "variables": {"admin_task": [
            "اعمل فحص شامل للنظام: مساحة القرص، استهلاك RAM، الخدمات الشغالة",
            "أنشئ systemd service جديدة لـ NOOGH مع auto-restart وlog rotation",
            "حسّن أداء النظام: اضبط swappiness، disk scheduler، network buffers",
            "اعمل firewall rules تسمح فقط ببورتات النظام المطلوبة",
            "أنشئ cron job للنسخ الاحتياطي اليومي الساعة 3 الفجر",
        ]}
    },
    # === Multi-step Complex Tasks ===
    {
        "category": "complex_task",
        "task": "نفذ المهمة التالية خطوة بخطوة مع استخدام الأدوات: {complex_task}",
        "variables": {"complex_task": [
            "اكتشف أي ملفات في المشروع أكبر من 10MB واقترح حلول لتقليل حجمها",
            "حلل كل ملفات Python في neural_engine/ واكتب تقرير عن جودة الكود",
            "ابحث عن أي أسرار مكشوفة (API keys, passwords) في الكود وقدم تقرير",
            "اعمل profiling للنظام واكتشف أكبر 5 bottlenecks",
            "صمم وحدة اختبار شاملة لـ model_authority.py",
        ]}
    },
]


# ─── Database ─────────────────────────────────────────────────

class TrajectoryDB:
    """SQLite database for storing teacher model trajectories."""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db_path))
        self._create_tables()
    
    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                total_tasks INTEGER DEFAULT 0,
                successful_tasks INTEGER DEFAULT 0,
                teacher_model TEXT,
                notes TEXT
            );
            
            CREATE TABLE IF NOT EXISTS trajectories (
                trajectory_id TEXT PRIMARY KEY,
                session_id TEXT REFERENCES sessions(session_id),
                task_category TEXT NOT NULL,
                task_prompt TEXT NOT NULL,
                system_prompt TEXT NOT NULL,
                
                -- Full conversation (messages format)
                messages_json TEXT NOT NULL,
                
                -- Teacher response
                teacher_response TEXT NOT NULL,
                
                -- Extracted tool calls
                tool_calls_json TEXT,
                
                -- Metadata
                input_tokens INTEGER,
                output_tokens INTEGER,
                latency_ms INTEGER,
                quality_score REAL,
                
                created_at TEXT NOT NULL,
                
                -- For training export
                exported INTEGER DEFAULT 0
            );
            
            CREATE INDEX IF NOT EXISTS idx_trajectories_category 
                ON trajectories(task_category);
            CREATE INDEX IF NOT EXISTS idx_trajectories_exported 
                ON trajectories(exported);
            CREATE INDEX IF NOT EXISTS idx_trajectories_quality 
                ON trajectories(quality_score DESC);
        """)
        self.conn.commit()
    
    def create_session(self, model: str, notes: str = "") -> str:
        session_id = str(uuid.uuid4())[:8]
        self.conn.execute(
            "INSERT INTO sessions (session_id, started_at, teacher_model, notes) VALUES (?,?,?,?)",
            (session_id, datetime.now().isoformat(), model, notes)
        )
        self.conn.commit()
        return session_id
    
    def end_session(self, session_id: str, total: int, successful: int):
        self.conn.execute(
            "UPDATE sessions SET ended_at=?, total_tasks=?, successful_tasks=? WHERE session_id=?",
            (datetime.now().isoformat(), total, successful, session_id)
        )
        self.conn.commit()
    
    def save_trajectory(self, session_id: str, category: str, task: str,
                       messages: list, response: str, tool_calls: list = None,
                       input_tokens: int = 0, output_tokens: int = 0,
                       latency_ms: int = 0, quality_score: float = 0.0):
        tid = str(uuid.uuid4())[:12]
        self.conn.execute("""
            INSERT INTO trajectories 
            (trajectory_id, session_id, task_category, task_prompt, system_prompt,
             messages_json, teacher_response, tool_calls_json,
             input_tokens, output_tokens, latency_ms, quality_score, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            tid, session_id, category, task, SYSTEM_PROMPT,
            json.dumps(messages, ensure_ascii=False),
            response,
            json.dumps(tool_calls or [], ensure_ascii=False),
            input_tokens, output_tokens, latency_ms, quality_score,
            datetime.now().isoformat()
        ))
        self.conn.commit()
        return tid
    
    def export_to_jsonl(self, output_path: str, min_quality: float = 0.5) -> int:
        """Export high-quality trajectories as JSONL training data."""
        cursor = self.conn.execute("""
            SELECT messages_json, teacher_response, task_category, quality_score
            FROM trajectories 
            WHERE quality_score >= ? AND exported = 0
            ORDER BY quality_score DESC
        """, (min_quality,))
        
        count = 0
        with open(output_path, 'w', encoding='utf-8') as f:
            for row in cursor:
                messages = json.loads(row[0])
                # Add assistant response
                messages.append({"role": "assistant", "content": row[1]})
                
                f.write(json.dumps({
                    "messages": messages,
                    "category": row[2],
                    "quality": row[3]
                }, ensure_ascii=False) + "\n")
                count += 1
        
        # Mark as exported
        self.conn.execute(
            "UPDATE trajectories SET exported = 1 WHERE quality_score >= ? AND exported = 0",
            (min_quality,)
        )
        self.conn.commit()
        
        logger.info(f"📦 Exported {count} trajectories to {output_path}")
        return count
    
    def get_stats(self) -> dict:
        cursor = self.conn.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN quality_score >= 0.7 THEN 1 END) as high_quality,
                AVG(quality_score) as avg_quality,
                SUM(output_tokens) as total_tokens,
                COUNT(DISTINCT task_category) as categories
            FROM trajectories
        """)
        row = cursor.fetchone()
        return {
            "total": row[0],
            "high_quality": row[1],
            "avg_quality": round(row[2] or 0, 2),
            "total_tokens": row[3] or 0,
            "categories": row[4] or 0
        }
    
    def close(self):
        self.conn.close()


# ─── Teacher Client ──────────────────────────────────────────

class TeacherClient:
    """Client for the remote Teacher model API (OpenAI compatible)."""
    
    def __init__(self, api_url: str, api_key: str = "EMPTY", model: str = "noogh-teacher"):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    
    def chat(self, messages: List[Dict], temperature: float = 0.7,
             max_tokens: int = 2048) -> Dict[str, Any]:
        """Send chat request to teacher model."""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        start = time.time()
        try:
            response = requests.post(
                f"{self.api_url}/v1/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            data = response.json()
            
            latency = int((time.time() - start) * 1000)
            
            return {
                "content": data["choices"][0]["message"]["content"],
                "input_tokens": data.get("usage", {}).get("prompt_tokens", 0),
                "output_tokens": data.get("usage", {}).get("completion_tokens", 0),
                "latency_ms": latency,
                "success": True,
            }
        except Exception as e:
            logger.error(f"❌ Teacher API error: {e}")
            return {"content": "", "success": False, "error": str(e)}
    
    def health_check(self) -> bool:
        """Check if teacher API is reachable."""
        try:
            r = requests.get(f"{self.api_url}/v1/models", 
                           headers=self.headers, timeout=5)
            return r.status_code == 200
        except:
            return False


# ─── Task Generator ──────────────────────────────────────────

def generate_tasks(count: int = 100) -> List[Dict]:
    """Generate diverse tasks from templates."""
    import random
    tasks = []
    
    for template in TASK_TEMPLATES:
        if "variables" not in template:
            tasks.append({
                "category": template["category"],
                "task": template["task"]
            })
            continue
        
        # Generate combinations
        variables = template["variables"]
        keys = list(variables.keys())
        
        if len(keys) == 1:
            for val in variables[keys[0]]:
                tasks.append({
                    "category": template["category"],
                    "task": template["task"].format(**{keys[0]: val})
                })
        elif len(keys) == 2:
            for v1 in variables[keys[0]]:
                for v2 in variables[keys[1]]:
                    tasks.append({
                        "category": template["category"],
                        "task": template["task"].format(**{keys[0]: v1, keys[1]: v2})
                    })
    
    random.shuffle(tasks)
    return tasks[:count]


# ─── Quality Scorer ──────────────────────────────────────────

def score_response(response: str, category: str) -> float:
    """Auto-score response quality (0.0 - 1.0)."""
    score = 0.0
    
    # Length check (responses should be substantial)
    if len(response) > 200: score += 0.2
    if len(response) > 500: score += 0.1
    if len(response) > 1000: score += 0.1
    
    # Tool usage (should use tools when appropriate)
    tool_indicators = ["file.read", "sys.exec", "sec.audit", "code.analyze",
                       "net.scan", "gpu.status", "mem.search", "plan.create"]
    tool_count = sum(1 for t in tool_indicators if t in response)
    if tool_count >= 1: score += 0.15
    if tool_count >= 2: score += 0.1
    
    # Structure (numbered steps, headers, etc.)
    if any(f"{i}." in response or f"{i})" in response for i in range(1, 6)):
        score += 0.1
    
    # Arabic content (should respond in Arabic)
    arabic_chars = sum(1 for c in response if '\u0600' <= c <= '\u06FF')
    if arabic_chars > 50: score += 0.1
    
    # Technical depth
    tech_terms = ["API", "GPU", "VRAM", "CPU", "RAM", "systemd", "docker",
                  "LoRA", "model", "endpoint", "token", "database"]
    tech_count = sum(1 for t in tech_terms if t.lower() in response.lower())
    if tech_count >= 3: score += 0.15
    
    return min(score, 1.0)


# ─── Main Runner ─────────────────────────────────────────────

class TrajectoryRunner:
    """Main orchestrator for running teacher sessions."""
    
    def __init__(self, api_url: str, api_key: str = "EMPTY"):
        self.teacher = TeacherClient(api_url, api_key)
        self.db = TrajectoryDB()
    
    def run_session(self, num_tasks: int = 50, notes: str = ""):
        """Run a full trajectory recording session."""
        
        # Health check
        if not self.teacher.health_check():
            logger.error("❌ Teacher API not reachable! Check NOOGH_TEACHER_URL")
            return
        
        logger.info(f"🎯 Starting session: {num_tasks} tasks")
        session_id = self.db.create_session(self.teacher.model, notes)
        
        tasks = generate_tasks(num_tasks)
        successful = 0
        
        for i, task_info in enumerate(tasks):
            task = task_info["task"]
            category = task_info["category"]
            
            logger.info(f"\n{'='*50}")
            logger.info(f"📋 Task {i+1}/{len(tasks)} [{category}]")
            logger.info(f"   {task[:80]}...")
            
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": task}
            ]
            
            result = self.teacher.chat(messages)
            
            if result["success"]:
                quality = score_response(result["content"], category)
                
                self.db.save_trajectory(
                    session_id=session_id,
                    category=category,
                    task=task,
                    messages=messages,
                    response=result["content"],
                    input_tokens=result.get("input_tokens", 0),
                    output_tokens=result.get("output_tokens", 0),
                    latency_ms=result.get("latency_ms", 0),
                    quality_score=quality
                )
                
                successful += 1
                logger.info(f"   ✅ Quality: {quality:.2f} | Tokens: {result.get('output_tokens', 0)} | {result.get('latency_ms', 0)}ms")
            else:
                logger.warning(f"   ❌ Failed: {result.get('error', 'Unknown')}")
            
            # Small delay to avoid rate limits
            time.sleep(1)
        
        self.db.end_session(session_id, len(tasks), successful)
        
        stats = self.db.get_stats()
        logger.info(f"\n{'='*50}")
        logger.info(f"📊 Session Complete!")
        logger.info(f"   Tasks: {successful}/{len(tasks)} successful")
        logger.info(f"   DB Total: {stats['total']} trajectories")
        logger.info(f"   Avg Quality: {stats['avg_quality']}")
        logger.info(f"   High Quality: {stats['high_quality']}")
        
        return session_id
    
    def export_dataset(self, output_path: str = None, min_quality: float = 0.5):
        """Export trajectories as training dataset."""
        if output_path is None:
            output_path = str(Path(__file__).parent.parent / "training_data" / "NOOGH_TEACHER_TRAJECTORIES.jsonl")
        
        count = self.db.export_to_jsonl(output_path, min_quality)
        logger.info(f"📦 Exported {count} samples to {output_path}")
    
    def close(self):
        self.db.close()


# ─── CLI ──────────────────────────────────────────────────────

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="NOOGH Trajectory Recorder")
    parser.add_argument("command", choices=["run", "export", "stats"],
                       help="Command to execute")
    parser.add_argument("--url", default=TEACHER_API_URL,
                       help="Teacher API URL (or set NOOGH_TEACHER_URL)")
    parser.add_argument("--key", default=TEACHER_API_KEY,
                       help="API key (or set NOOGH_TEACHER_KEY)")
    parser.add_argument("--tasks", type=int, default=50,
                       help="Number of tasks to run")
    parser.add_argument("--min-quality", type=float, default=0.5,
                       help="Minimum quality score for export")
    parser.add_argument("--output", default=None,
                       help="Output JSONL path for export")
    parser.add_argument("--notes", default="",
                       help="Session notes")
    
    args = parser.parse_args()
    
    if args.command == "run":
        if not args.url:
            print("❌ Set NOOGH_TEACHER_URL or use --url")
            print("   Example: --url https://your-pod-8000.proxy.runpod.net")
            return
        
        runner = TrajectoryRunner(args.url, args.key)
        runner.run_session(args.tasks, args.notes)
        runner.close()
    
    elif args.command == "export":
        db = TrajectoryDB()
        count = db.export_to_jsonl(
            args.output or "training_data/NOOGH_TEACHER_TRAJECTORIES.jsonl",
            args.min_quality
        )
        print(f"✅ Exported {count} samples")
        db.close()
    
    elif args.command == "stats":
        db = TrajectoryDB()
        stats = db.get_stats()
        print(f"\n📊 Trajectory Database Stats:")
        print(f"   Total trajectories: {stats['total']}")
        print(f"   High quality (≥0.7): {stats['high_quality']}")
        print(f"   Average quality: {stats['avg_quality']}")
        print(f"   Total tokens: {stats['total_tokens']:,}")
        print(f"   Categories: {stats['categories']}")
        db.close()


if __name__ == "__main__":
    main()
