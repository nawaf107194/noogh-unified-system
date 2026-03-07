import json
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

MAX_HISTORY = 20
MAX_TEXT_SIZE = 8192


@dataclass
class SessionTaskSummary:
    task_id: str
    input_summary: str
    result_summary: str
    timestamp: float
    mode: str


@dataclass
class AgentSession:
    session_id: str
    created_at: float
    updated_at: float
    tasks: List[SessionTaskSummary] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SessionStore:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _get_path(self, session_id: str) -> str:
        safe_id = os.path.basename(session_id)
        return os.path.join(self.base_dir, f"{safe_id}.json")

    def create_session(self) -> AgentSession:
        session_id = str(uuid.uuid4())
        now = time.time()
        session = AgentSession(session_id=session_id, created_at=now, updated_at=now)
        self.save_session(session)
        return session

    def get_session(self, session_id: str) -> Optional[AgentSession]:
        path = self._get_path(session_id)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r") as f:
                data = json.load(f)
            tasks = [SessionTaskSummary(**t) for t in data.get("tasks", [])]
            return AgentSession(
                session_id=data["session_id"],
                created_at=data["created_at"],
                updated_at=data["updated_at"],
                tasks=tasks,
                metadata=data.get("metadata", {}),
            )
        except Exception:
            return None

    def save_session(self, session: AgentSession):
        path = self._get_path(session.session_id)
        session.updated_at = time.time()
        if len(session.tasks) > MAX_HISTORY:
            session.tasks = session.tasks[-MAX_HISTORY:]
        with open(path, "w") as f:
            json.dump(asdict(session), f, indent=2)

    def add_task(self, session_id: str, task_input: str, result_summary: str, mode: str) -> None:
        session = self.get_session(session_id)
        if not session:
            return
        safe_input = task_input[:MAX_TEXT_SIZE]
        safe_result = str(result_summary)[:MAX_TEXT_SIZE]
        task_summary = SessionTaskSummary(
            task_id=str(uuid.uuid4()),
            input_summary=safe_input,
            result_summary=safe_result,
            timestamp=time.time(),
            mode=mode,
        )
        session.tasks.append(task_summary)
        self.save_session(session)


def get_session_store(data_dir: str) -> SessionStore:
    """Factory for SessionStore."""
    if not data_dir:
        raise ValueError("data_dir is required")
    base_dir = os.path.join(data_dir, ".noogh_memory", "sessions")
    return SessionStore(base_dir=base_dir)
