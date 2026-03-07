import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

from gateway.app.core.filelock import file_lock
from gateway.app.core.logging import get_logger

logger = get_logger("audit")


class AuditLogger:
    def __init__(self, data_dir: str):
        if not data_dir:
            raise ValueError("data_dir is required for AuditLogger")
        self.audit_dir = Path(data_dir) / ".noogh_audit"
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.audit_dir / "audit.jsonl"

    def log_task(self, task_id: str, input_text: str, protocol_result: str, exec_summary: str):
        input_hash = hashlib.sha256(input_text.encode()).hexdigest()
        record = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "input_sha256": input_hash,
            "protocol_result": protocol_result,
            "exec_summary": exec_summary,
        }
        with open(self.log_file, "a") as f:
            with file_lock(f):
                f.write(json.dumps(record) + "\n")
                f.flush()
                os.fsync(f.fileno())
        logger.info(f"Audit log entry added for task {task_id}")


def get_audit_logger(data_dir: str) -> AuditLogger:
    """Factory for AuditLogger."""
    return AuditLogger(data_dir=data_dir)
