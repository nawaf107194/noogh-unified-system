#!/home/noogh/projects/noogh_unified_system/src/.venv/bin/python3
"""
Local Knowledge Harvester Agent
-------------------------------
Crawls the user's local directories (projects, Documents, etc.) to learn from 
local codebases and documentation, injecting the knowledge into NOOGH's shared memory.
"""

import sys
import os
import time
import json
import sqlite3
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Set, Any

# Add project path
sys.path.insert(0, "/home/noogh/projects/noogh_unified_system/src")
sys.path.append(str(Path(__file__).parent.parent))

from unified_core.neural_bridge import NeuralEngineClient
import asyncio
import re

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | local_harvester | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/home/noogh/projects/noogh_unified_system/src/logs/local_harvester.log"),
    ]
)
logger = logging.getLogger("local_harvester")

HOME = str(Path.home())
TARGET_DIRS = [
    os.path.join(HOME, "projects"),
    os.path.join(HOME, "Documents"),
    "/home/noogh/projects/noogh_unified_system/src/system-prompts-and-models-of-ai-tools-main"
]
ALLOWED_EXTENSIONS = {'.md', '.txt', '.py', '.rs', '.go', '.js', '.json', '.yml', '.yaml', '.sh', '.cpp', '.h'}
MAX_FILE_SIZE_BYTES = 1024 * 1024  # 1MB max per file to allow for deep context processing

DB_PATH = "/home/noogh/projects/noogh_unified_system/src/data/shared_memory.sqlite"
SEEN_FILE = os.path.join(HOME, ".noogh", "local_harvester_seen.json")


class LocalKnowledgeHarvester:
    def __init__(self):
        self._seen_files: Dict[str, float] = self._load_seen()
        os.environ["VLLM_MODEL_NAME"] = "qwen2.5:7b"
        logger.info(f"📂 Local Harvester initialized | Tracking {len(self._seen_files)} files")

    def _load_seen(self) -> Dict[str, float]:
        Path(SEEN_FILE).parent.mkdir(parents=True, exist_ok=True)
        try:
            return json.load(open(SEEN_FILE))
        except Exception:
            return {}

    def _save_seen(self):
        try:
            with open(SEEN_FILE, "w") as f:
                json.dump(self._seen_files, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save seen files: {e}")

    def scan_directories(self) -> List[str]:
        """Find new or modified files in target directories"""
        files_to_process = []
        for d in TARGET_DIRS:
            if not os.path.exists(d):
                continue
            
            logger.info(f"🔍 Scanning directory: {d}")
            for root, _, files in os.walk(d):
                # Skip hidden directories like .git
                if '/.' in root:
                    continue
                    
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext not in ALLOWED_EXTENSIONS:
                        continue
                        
                    file_path = os.path.join(root, file)
                    try:
                        stat = os.stat(file_path)
                        if stat.st_size > MAX_FILE_SIZE_BYTES or stat.st_size < 10:
                            continue  # Skip too large or empty
                            
                        last_mtime = self._seen_files.get(file_path, 0)
                        if stat.st_mtime > last_mtime:
                            files_to_process.append(file_path)
                    except Exception:
                        pass
        
        # Sort by modification time (newest first)
        files_to_process.sort(key=lambda x: os.stat(x).st_mtime, reverse=True)
        return files_to_process

    def read_file_content(self, file_path: str) -> Optional[str]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return content
        except UnicodeDecodeError:
            # Not a text file
            return None
        except Exception as e:
            logger.debug(f"Error reading {file_path}: {e}")
            return None

    async def _extract_concepts_with_brain(self, file_name: str, content: str) -> Optional[Dict[str, Any]]:
        prompt = f"""You are NOOGH's Local Knowledge Harvester.
Read the following local file content deeply. 
Analyze the technical concepts, system instructions, architecture, or code logic within it.
Return a valid JSON object with EXACTLY two keys:
1. "tags": A JSON array of 1 to 4 strings representing the TOP technical tags that describe this file.
2. "deep_summary": A deep, concise paragraph explaining the most critical technical takeaways, patterns, or system prompts you learned from this file.

File Name: {file_name}
File Content:
{content[:15000]}
"""
        try:
            async with NeuralEngineClient(base_url="http://localhost:11434", mode="vllm") as bridge:
                resp = await bridge.think(prompt, depth="standard")
                content_resp = resp.get("content", "").strip()
                
                # Extract the JSON block
                match = re.search(r'\{.*\}', content_resp, re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                    tags = data.get("tags", [])
                    summary = data.get("deep_summary", "")
                    if isinstance(tags, list) and len(tags) > 0:
                        return {"tags": [str(t) for t in tags[:4]], "deep_summary": summary}
                return None
        except Exception as e:
            logger.warning(f"⚠️ Brain failed to extract concepts: {e}")
            return None

    def inject_to_noogh(self, file_path: str, content: str, extraction: Dict[str, Any]) -> bool:
        tags = extraction.get("tags", [])
        deep_summary = extraction.get("deep_summary", "")
        
        if not tags:
            return False
            
        try:
            conn = sqlite3.connect(DB_PATH, timeout=10)
            cur = conn.cursor()

            # ① Observation
            obs_key = f"local_file_{hashlib.md5(file_path.encode()).hexdigest()[:10]}_{int(time.time())}"
            obs_val = json.dumps({
                "source": "local_harvester",
                "type": "local_file_content",
                "title": os.path.basename(file_path),
                "path": file_path,
                "tags": tags,
                "deep_summary": deep_summary,
                "transcript": content[:800],
                "quality": "HIGH" if len(content) > 500 else "MEDIUM",
                "topic": "local_knowledge"
            }, ensure_ascii=False)
            
            cur.execute(
                "INSERT OR REPLACE INTO observations (key, value, timestamp) VALUES (?, ?, ?)",
                (obs_key, obs_val, time.time())
            )

            # ② Update Beliefs
            for tag in tags:
                belief_key = f"learned_concept:{tag}"
                cur.execute("SELECT value, utility_score FROM beliefs WHERE key=?", (belief_key,))
                row = cur.fetchone()
                
                learned_time = datetime.now().isoformat()
                
                if row:
                    try:
                        old_val = json.loads(row[0])
                    except Exception:
                        old_val = {}
                    new_val = {**old_val, "count": old_val.get("count", 1) + 1, "last_seen": learned_time}
                    new_utility = min(0.95, float(row[1] or 0.5) + 0.05)
                    cur.execute(
                        "UPDATE beliefs SET value=?, utility_score=?, updated_at=? WHERE key=?",
                        (json.dumps(new_val), new_utility, time.time(), belief_key)
                    )
                    logger.info(f"  📈 Belief reinforced: {tag} (utility={new_utility:.2f})")
                else:
                    belief_val = json.dumps({
                        "concept": tag,
                        "source": "local_harvester",
                        "file": os.path.basename(file_path),
                        "count": 1,
                        "first_seen": learned_time,
                    })
                    cur.execute(
                        "INSERT INTO beliefs (key, value, utility_score, updated_at) VALUES (?,?,?,?)",
                        (belief_key, belief_val, 0.65, time.time())
                    )
                    logger.info(f"  🆕 New belief: {tag}")

            conn.commit()
            conn.close()
            logger.info(f"  ✅ Injected file: {os.path.basename(file_path)}")
            return True

        except sqlite3.OperationalError as e:
            logger.warning(f"  ⚠️ DB issue: {e}")
            return False
        except Exception as e:
            logger.error(f"  ❌ DB injection error: {e}")
            return False

    def run_once(self, max_files: int = 5):
        logger.info("═══════════════════════════════════════════════════════")
        logger.info(f"📂 LOCAL HARVESTING CYCLE | {datetime.now().strftime('%H:%M:%S')}")
        logger.info("═══════════════════════════════════════════════════════")
        
        files = self.scan_directories()
        logger.info(f"  Found {len(files)} new/modified files to process")

        processed_count = 0
        for file_path in files[:max_files]:
            logger.info(f"\n📄 Processing: {file_path}")
            content = self.read_file_content(file_path)
            
            if not content:
                logger.debug(f"  ⏭️ Skipped: Cannot read text")
                # mark as seen so we don't keep trying
                try: 
                    self._seen_files[file_path] = os.stat(file_path).st_mtime
                except Exception: pass
                continue
                
            extraction = asyncio.run(self._extract_concepts_with_brain(os.path.basename(file_path), content))
            if extraction and extraction.get("tags"):
                logger.info(f"  🧠 Tags: {extraction['tags']}")
                logger.info(f"  💡 Deep Summary: {extraction['deep_summary'][:150]}...")
                success = self.inject_to_noogh(file_path, content, extraction)
                if success:
                    processed_count += 1
            else:
                logger.info(f"  ⏭️ Skipped: No concepts extracted")
            
            # Update mtime in seen dict
            try:
                self._seen_files[file_path] = os.stat(file_path).st_mtime
                self._save_seen()
            except Exception:
                pass

        logger.info(f"\n✅ Cycle complete | Harvested {processed_count} local files")

if __name__ == "__main__":
    agent = LocalKnowledgeHarvester()
    # Process up to 5 files per test run
    agent.run_once(max_files=5)
