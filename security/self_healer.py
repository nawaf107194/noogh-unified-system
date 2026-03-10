"""
🧬 NOOGH Self-Healer (Robust Evolution Layer)
-------------------------------------------
This system grants NOOGH the ability to modify its own source code safely.
1. Scans project files for performance issues or bugs.
2. Generates optimized/fixed code via LLM using robust JSON extraction.
3. Tests generated code in isolation (Syntax Check via AST).
4. Creates timestamped backups before applying code evolution.
5. Records improvements as 'beliefs' in the shared memory database.

Governance: v5.4 (Self-Correcting)
"""

import sys
import os
import json
import time
import logging
import re
import shutil
import subprocess
import ast
import argparse
import urllib.request
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Determine project root and add to path
SRC = "/home/noogh/projects/noogh_unified_system/src"
if SRC not in sys.path:
    sys.path.insert(0, SRC)

# Optional belief injection (if available)
try:
    from unified_core.brain_tools import db_inject_belief
    BELIEF_AVAILABLE = True
except ImportError:
    BELIEF_AVAILABLE = False

# Setup logging
LOG_DIR = f"{SRC}/logs"
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"{LOG_DIR}/self_healer.log", mode='a')
    ]
)
logger = logging.getLogger("healer")

# Environment & Constants
VLLM_URL = os.environ.get("NEURAL_ENGINE_URL", "http://localhost:11434")
MODEL = os.environ.get("VLLM_MODEL_NAME", "qwen2.5-coder:7b")
EXCLUDE_DIRS = {"__pycache__", "venv", "env", ".git", "logs", "data", "backups", ".noogh_venv", ".pytest_cache"}
EXCLUDE_FILES = {"__init__.py", "self_healer.py"}

class SelfHealer:
    def __init__(self, target_dirs: List[str] = None):
        if target_dirs is None:
            self.target_dirs = [f"{SRC}/agents", f"{SRC}/unified_core"]
        else:
            self.target_dirs = target_dirs
        
        self.backup_dir = f"{SRC}/backups/healer_backups"
        os.makedirs(self.backup_dir, exist_ok=True)
        
        logger.info("🧬 Self-Healer initialized (Robust Evolution Layer active)")
        logger.info(f"   Model: {MODEL} | Memory: {VLLM_URL}")
        logger.info("───────────────────────────────────────────────────────")

    def _safe_json_extract(self, content: str) -> Dict:
        """Robustly extract JSON from LLM response using fallback methods."""
        # 1. Direct parse attempt
        try:
            return json.loads(content)
        except:
            pass

        # 2. Extract first valid {...} block
        match = re.search(r'\{[\s\S]*\}', content)
        if not match:
            logger.warning("  ⚠️ No JSON block found in brain response.")
            return {}

        raw = match.group()
        # Clean markdown artifacts
        raw = raw.replace("```json", "").replace("```python", "").replace("```", "").strip()
        # Fix trailing commas
        raw = re.sub(r',\s*([\]}])', r'\1', raw)

        # 3. Try standard JSON again
        try:
            return json.loads(raw)
        except Exception as e:
            # 4. Final fallback using AST (handles python-style dicts if LLM uses ' instead of ")
            try:
                parsed = ast.literal_eval(raw)
                if isinstance(parsed, dict):
                    return parsed
            except:
                logger.error(f"  ❌ Robust JSON extraction failed. Raw error: {e}")

        return {}

    def _ask_brain_for_code(self, prompt: str) -> Dict:
        """Consult the Neural Engine for code improvements."""
        payload = {
            "model": MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "أنت مهندس برمجيات ومهندس ذكاء اصطناعي مكلف بتحسين أو إصلاح كود NOOGH.\n"
                        "المهمة: ابحث عن العيوب وقدم الكود الكامل المحدث.\n"
                        "يجب أن تكون الإجابة بصيغة JSON حصراً بالتنسيق التالي:\n"
                        "{\n"
                        "  'needs_refactor': true/false,\n"
                        "  'issue_found': 'وصف المشكلة في سطرين',\n"
                        "  'new_code': 'الكود الكامل المحدث (بدون علامات ```)',\n"
                        "  'confidence': 0.95\n"
                        "}"
                    )
                },
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 5000,
            "temperature": 0.2,
            "stream": False,
        }

        try:
            body = json.dumps(payload).encode()
            req = urllib.request.Request(
                f"{VLLM_URL}/v1/chat/completions",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=180) as r:
                raw_response = r.read().decode('utf-8')
                data = json.loads(raw_response)
                content = data["choices"][0]["message"]["content"].strip()
                return self._safe_json_extract(content)
        except Exception as e:
            logger.error(f"  ❌ Brain Connection Failure: {e}")
            return {}

    def _syntax_check(self, code: str, file_path: str) -> bool:
        """Verify generated code syntax before applying."""
        try:
            ast.parse(code, filename=file_path)
            return True
        except SyntaxError as e:
            logger.error(f"    💥 Syntax Error at line {e.lineno}: {e.msg}")
            return False
        except Exception as e:
            logger.error(f"    💥 Validation failed: {e}")
            return False

    def _backup_file(self, file_path: str) -> bool:
        """Create a timestamped backup."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = os.path.basename(file_path)
        backup_path = os.path.join(self.backup_dir, f"{base}.{timestamp}.bak")
        try:
            shutil.copy2(file_path, backup_path)
            logger.info(f"    ✅ Backup created: {os.path.basename(backup_path)}")
            return True
        except Exception as e:
            logger.error(f"    ❌ Backup failed: {e}")
            return False

    def analyze_and_refactor(self, file_path: str) -> bool:
        """Read, analyze, test, and safely evolve a single file."""
        filename = os.path.basename(file_path)
        if filename in EXCLUDE_FILES:
            return False

        logger.info(f"  🔍 Analyzing {filename} for potential evolution...")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                current_code = f.read()
            
            if len(current_code) > 20000:
                logger.info("    ℹ️ File too large for direct evolution, skipping.")
                return False

        except Exception as e:
            logger.error(f"  ❌ Failed to read {filename}: {e}")
            return False

        prompt = f"""هذا كود مصدري من نظام (NOOGH):
الملف: {filename}

الكود الحالي:
```python
{current_code}
```

المطلوب:
1. ابحث عن أي ثغرات برمجية، مشاكل في الأداء، أو عدم دقة في التعامل مع الأخطاء.
2. إذا كان الكود ممتازاً، أرجع 'needs_refactor': false.
3. إذا وجدت تحسيناً، أخرج الكود الشامل المحسن في 'new_code'."""

        response = self._ask_brain_for_code(prompt)

        if not response.get("needs_refactor", False):
            logger.info("    ✔️ Code is optimal according to current neural assessment.")
            return False

        if response.get("confidence", 0) < 0.85:
            logger.info(f"    ⚠️ Low confidence ({response.get('confidence')}), skipping evolution.")
            return False

        new_code = response.get("new_code", "").strip()
        if not new_code or len(new_code) < (len(current_code) * 0.1): # sanity check: code shouldn't shrink too much
            logger.warning("    ⚠️ Generated code suspiciously small or empty. Aborting.")
            return False

        logger.info(f"    🛠️ Issue identified: {response.get('issue_found')}")
        logger.info("    🧪 Verifying synthesized code...")

        if not self._syntax_check(new_code, file_path):
            return False

        # Apply evolution
        if not self._backup_file(file_path):
            return False

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_code)
            
            logger.info(f"    ✅ Evolution applied to {filename} successfully.")
            
            if BELIEF_AVAILABLE:
                db_inject_belief(
                    f"evolution:success:{filename}",
                    {"issue": response.get("issue_found"), "timestamp": time.time()},
                    utility=0.98
                )
            return True

        except Exception as e:
            logger.error(f"    ❌ Failed to overwrite file: {e}")
            return False

    def hunt_for_evolution(self, max_files: int = 1):
        """Strategic scan for code evolution opportunities."""
        import random
        all_files = []
        for d in self.target_dirs:
            if not os.path.exists(d): continue
            for root, dirs, files in os.walk(d):
                # Prune excluded directories
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
                for f in files:
                    if f.endswith(".py") and f not in EXCLUDE_FILES and not f.startswith("test_"):
                        all_files.append(os.path.join(root, f))
        
        if not all_files:
            logger.info("    ℹ️ No candidate files found for evolution.")
            return

        targets = random.sample(all_files, min(max_files, len(all_files)))
        count = 0
        for target in targets:
            if self.analyze_and_refactor(target):
                count += 1
        
        if count > 0:
            logger.info(f"🧬 Evolution cycle complete: {count} improvements applied.")
        else:
            logger.info("🧬 Evolution cycle complete: No changes required.")

def main():
    parser = argparse.ArgumentParser(description="NOOGH Robust Self-Healer")
    parser.add_argument("--once", action="store_true", help="Run a single evolution pass")
    parser.add_argument("--interval", type=int, default=1800, help="Loop interval in seconds (default: 1800)")
    parser.add_argument("--files", type=int, default=2, help="Number of files to scan per pass")
    args = parser.parse_args()

    healer = SelfHealer()
    
    if args.once:
        healer.hunt_for_evolution(max_files=args.files)
    else:
        logger.info(f"🧬 Starting background evolution loop (Interval: {args.interval}s)")
        while True:
            healer.hunt_for_evolution(max_files=args.files)
            time.sleep(args.interval)

if __name__ == "__main__":
    main()