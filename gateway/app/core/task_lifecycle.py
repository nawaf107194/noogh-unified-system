import json
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class TaskState(str, Enum):
    RECEIVED = "RECEIVED"
    CLASSIFIED = "CLASSIFIED"
    PLANNED = "PLANNED"
    EXECUTED = "EXECUTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


@dataclass
class TaskRecord:
    task_id: str
    session_id: Optional[str]
    input_text: str
    state: TaskState
    lifecycle_events: List[str]
    created_at: float
    updated_at: float


class TaskLifecycle:
    def __init__(self, task_id: str, session_id: Optional[str], input_text: str, data_dir: str):
        self.task_id = task_id
        self.session_id = session_id
        self.input_text = input_text
        self.state = TaskState.RECEIVED
        self.events = [TaskState.RECEIVED.value]

        if not data_dir:
            data_dir = "."

        self.task_dir = os.path.join(data_dir, ".noogh_memory", "tasks", task_id)
        os.makedirs(self.task_dir, exist_ok=True)
        self.created_at = time.time()
        self._save_metadata()

    def transition(self, new_state: TaskState, info: str = None):
        if info:
            self.events.append(f"{new_state.value}: {info}")
        else:
            self.events.append(new_state.value)
        self.state = new_state
        self._save_metadata()

    def save_artifact(self, filename: str, content: str):
        path = os.path.join(self.task_dir, filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        text = str(content)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    def _save_metadata(self):
        with open(os.path.join(self.task_dir, "metadata.json"), "w") as f:
            json.dump(
                {
                    "task_id": self.task_id,
                    "session_id": self.session_id,
                    "state": self.state.value,
                    "lifecycle": self.events,
                },
                f,
                indent=2,
            )

    def get_lifecycle_list(self) -> List[str]:
        return self.events
