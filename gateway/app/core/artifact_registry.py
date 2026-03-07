import hashlib
import json
import os
import time
import uuid
from dataclasses import asdict, dataclass
from typing import List, Optional


@dataclass
class ArtifactRecord:
    artifact_id: str
    type: str
    path: str
    created_at: float
    session_id: Optional[str] = None
    job_id: Optional[str] = None
    size_bytes: int = 0
    sha256: Optional[str] = None


class ArtifactRegistry:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.registry_dir = os.path.join(data_dir, ".noogh_memory", "registry")
        self.index_file = os.path.join(self.registry_dir, "artifacts.jsonl")
        os.makedirs(self.registry_dir, exist_ok=True)
        if not os.path.exists(self.index_file):
            with open(self.index_file, "w") as f:
                pass

    def register(
        self, type: str, relative_path: str, session_id: Optional[str] = None, job_id: Optional[str] = None
    ) -> ArtifactRecord:

        memory_dir = os.path.join(self.data_dir, ".noogh_memory")
        full_path = os.path.join(memory_dir, relative_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Artifact not found: {full_path}")

        size = os.path.getsize(full_path)
        with open(full_path, "rb") as f:
            sha = hashlib.sha256(f.read()).hexdigest()

        record = ArtifactRecord(
            artifact_id=str(uuid.uuid4()),
            type=type,
            path=relative_path,
            created_at=time.time(),
            session_id=session_id,
            job_id=job_id,
            size_bytes=size,
            sha256=sha,
        )

        with open(self.index_file, "a") as f:
            f.write(json.dumps(asdict(record)) + "\n")

        return record

    def list_artifacts(self, limit: int = 50) -> List[ArtifactRecord]:
        records = []
        if os.path.exists(self.index_file):
            with open(self.index_file, "r") as f:
                lines = f.readlines()
                for line in reversed(lines[-limit:]):
                    try:
                        records.append(ArtifactRecord(**json.loads(line)))
                    except Exception:
                        pass
        return records

    def get_artifact(self, artifact_id: str) -> Optional[ArtifactRecord]:
        if os.path.exists(self.index_file):
            with open(self.index_file, "r") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        if data["artifact_id"] == artifact_id:
                            return ArtifactRecord(**data)
                    except Exception:
                        pass
        return None


def get_artifact_registry(data_dir: str) -> ArtifactRegistry:
    """Factory for ArtifactRegistry."""
    if not data_dir:
        raise ValueError("data_dir is required")
    return ArtifactRegistry(data_dir=data_dir)
