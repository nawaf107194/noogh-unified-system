import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from gateway.app.core.filelock import file_lock
from gateway.app.core.logging import get_logger

logger = get_logger("persistent_memory")


def _atomic_write_json(path: str, data: Any) -> None:
    path_obj = Path(path)
    dir_ = path_obj.parent
    dir_.mkdir(parents=True, exist_ok=True)
    lock_path = str(path_obj) + ".lock"
    with open(lock_path, "w") as lock_fp:
        with file_lock(lock_fp):
            fd, tmp_path = tempfile.mkstemp(prefix=".tmp_", dir=str(dir_))
            try:
                with os.fdopen(fd, "w") as tmp_fp:
                    json.dump(data, tmp_fp, ensure_ascii=False, indent=2)
                    tmp_fp.flush()
                    os.fsync(tmp_fp.fileno())
                os.replace(tmp_path, str(path_obj))
            except Exception as e:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                raise e


@dataclass
class TaskRecord:
    task_id: str
    task: str
    timestamp: str
    success: bool
    answer: str
    steps: int
    error: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class ConversationTurn:
    timestamp: str
    role: str
    content: str
    metadata: Dict[str, Any] = None


class PersistentMemory:
    def __init__(self, storage_dir: str):
        self.storage_dir = storage_dir
        self.storage_path = Path(self.storage_dir)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.tasks_file = self.storage_path / "tasks.json"
        self.conversations_file = self.storage_path / "conversations.json"
        logger.info(f"Persistent memory initialized: {self.storage_dir}")

    def save_task(self, task_record: TaskRecord):
        tasks = self._load_tasks()
        tasks.append(asdict(task_record))
        _atomic_write_json(str(self.tasks_file), tasks)

    def load_tasks(self, limit: int = 10) -> List[TaskRecord]:
        tasks_data = self._load_tasks()
        recent = tasks_data[-limit:] if len(tasks_data) > limit else tasks_data
        return [TaskRecord(**task) for task in recent]

    def _load_tasks(self) -> List[Dict]:
        if not self.tasks_file.exists():
            return []
        with open(self.tasks_file, "r") as f:
            return json.load(f)

    def get_task_stats(self) -> Dict[str, Any]:
        tasks = self._load_tasks()
        if not tasks:
            return {"total": 0, "success_rate": 0, "avg_steps": 0}
        total = len(tasks)
        successful = sum(1 for t in tasks if t.get("success", False))
        avg_steps = sum(t.get("steps", 0) for t in tasks) / total if total > 0 else 0
        return {
            "total": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "avg_steps": round(avg_steps, 2),
        }

    def save_conversation(self, session_id: str, turns: List[ConversationTurn]):
        conversations = self._load_conversations()
        session_data = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "turns": [asdict(turn) for turn in turns],
        }
        existing_idx = next((i for i, conv in enumerate(conversations) if conv.get("session_id") == session_id), None)
        if existing_idx is not None:
            conversations[existing_idx] = session_data
        else:
            conversations.append(session_data)
        if len(conversations) > 50:
            conversations = conversations[-50:]
        _atomic_write_json(str(self.conversations_file), conversations)

    def load_conversation(self, session_id: str) -> Optional[List[ConversationTurn]]:
        conversations = self._load_conversations()
        session = next((conv for conv in conversations if conv.get("session_id") == session_id), None)
        if not session:
            return None
        return [ConversationTurn(**turn) for turn in session["turns"]]

    def _load_conversations(self) -> List[Dict]:
        if not self.conversations_file.exists():
            return []
        with open(self.conversations_file, "r") as f:
            return json.load(f)

    def clear_all(self):
        if self.tasks_file.exists():
            self.tasks_file.unlink()
        if self.conversations_file.exists():
            self.conversations_file.unlink()

    def export_memory(self, output_file: str):
        export_data = {
            "tasks": self._load_tasks(),
            "conversations": self._load_conversations(),
            "exported_at": datetime.now().isoformat(),
        }
        with open(output_file, "w") as f:
            json.dump(export_data, f, indent=2)


def get_persistent_memory_legacy(data_dir: str) -> PersistentMemory:
    """Factory for legacy persistent memory (logs)."""
    if not data_dir:
        raise ValueError("data_dir is required")
    storage_dir = os.path.join(data_dir, ".noogh_memory")
    return PersistentMemory(storage_dir=storage_dir)
