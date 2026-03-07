import json
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Dict, List, Optional


def get_job_dir(data_dir: str) -> str:
    """Helper to get job directory from data_dir."""
    return os.path.join(data_dir, ".noogh_memory", "jobs")


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


@dataclass
class JobBudget:
    max_total_time_ms: int
    max_steps: int
    max_bytes_read: int = 10 * 1024 * 1024
    max_files_read: int = 20
    max_write_bytes: int = 2 * 1024 * 1024


@dataclass
class JobRequest:
    task: str
    mode: str
    budgets: JobBudget
    session_id: Optional[str] = None
    job_type: str = "agent_task"  # "agent_task" or "plan_execution"


@dataclass
class JobRecord:
    job_id: str
    request: JobRequest
    status: JobStatus
    created_at: float
    updated_at: float
    result: Optional[str] = None
    error: Optional[str] = None
    metrics: Dict[str, float] = field(default_factory=dict)
    signature: Optional[str] = None


def compute_job_signature(job_msg: str, secret: str) -> str:
    import hashlib
    import hmac

    return hmac.new(secret.encode(), job_msg.encode(), hashlib.sha256).hexdigest()


def sign_job_record(job: JobRecord, secret: str):
    import json
    
    req_dict = {
        "task": job.request.task,
        "mode": job.request.mode,
        "job_type": job.request.job_type,
        "budgets": {
            "max_total_time_ms": job.request.budgets.max_total_time_ms,
            "max_steps": job.request.budgets.max_steps,
            "max_bytes_read": job.request.budgets.max_bytes_read,
            "max_files_read": job.request.budgets.max_files_read,
            "max_write_bytes": job.request.budgets.max_write_bytes,
        },
        "session_id": job.request.session_id,
    }
    canonical_payload = json.dumps(req_dict, sort_keys=True, separators=(",", ":"))
    signature_input = f"{job.job_id}:{canonical_payload}"
    job.signature = compute_job_signature(signature_input, secret)


def verify_job_record(job: JobRecord, secret: str) -> bool:
    if not job.signature:
        return False
    import json

    req_dict = {
        "task": job.request.task,
        "mode": job.request.mode,
        "job_type": job.request.job_type,
        "budgets": {
            "max_total_time_ms": job.request.budgets.max_total_time_ms,
            "max_steps": job.request.budgets.max_steps,
            "max_bytes_read": job.request.budgets.max_bytes_read,
            "max_files_read": job.request.budgets.max_files_read,
            "max_write_bytes": job.request.budgets.max_write_bytes,
        },
        "session_id": job.request.session_id,
    }
    canonical_payload = json.dumps(req_dict, sort_keys=True, separators=(",", ":"))
    signature_input = f"{job.job_id}:{canonical_payload}"
    expected = compute_job_signature(signature_input, secret)
    import hmac

    return hmac.compare_digest(job.signature, expected)


class BaseJobStore:
    def submit_job(self, request: JobRequest) -> str:
        raise NotImplementedError

    def get_job(self, job_id: str) -> Optional[JobRecord]:
        raise NotImplementedError

    def save_job(self, job: JobRecord):
        raise NotImplementedError

    def list_queued_jobs(self) -> List[str]:
        raise NotImplementedError

    def list_jobs(self, limit: int = 50) -> List[JobRecord]:
        raise NotImplementedError

    def check_health(self) -> bool:
        raise NotImplementedError


class FileJobStore(BaseJobStore):
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
        self.queue_file = os.path.join(self.base_dir, "queue.jsonl")
        if not os.path.exists(self.queue_file):
            with open(self.queue_file, "w") as f:
                pass

    def check_health(self) -> bool:
        return True

    def _get_job_dir(self, job_id: str) -> str:
        return os.path.join(self.base_dir, job_id)

    def submit_job(self, request: JobRequest) -> str:
        job_id = str(uuid.uuid4())
        job = JobRecord(
            job_id=job_id, request=request, status=JobStatus.QUEUED, created_at=time.time(), updated_at=time.time()
        )
        job_dir = self._get_job_dir(job_id)
        os.makedirs(job_dir, exist_ok=True)
        os.makedirs(os.path.join(job_dir, "artifacts"), exist_ok=True)
        self.save_job(job)
        if hasattr(self, "secrets") and self.secrets.get("NOOGH_JOB_SIGNING_SECRET"):
             secret = self.secrets.get("NOOGH_JOB_SIGNING_SECRET")
             sign_job_record(job, secret)

        with open(self.queue_file, "a") as f:
            f.write(json.dumps({"job_id": job_id, "created_at": job.created_at}) + "\n")
        return job_id

    def get_job(self, job_id: str) -> Optional[JobRecord]:
        job_dir = self._get_job_dir(job_id)
        status_path = os.path.join(job_dir, "status.json")
        if not os.path.exists(status_path):
            return None
        try:
            with open(status_path, "r") as f:
                data = json.load(f)
            budgets_data = data["request"].pop("budgets")
            budgets = JobBudget(**budgets_data)
            request = JobRequest(budgets=budgets, **data["request"])
            return JobRecord(
                job_id=data["job_id"],
                request=request,
                status=JobStatus(data["status"]),
                created_at=data["created_at"],
                updated_at=data["updated_at"],
                result=data.get("result"),
                error=data.get("error"),
                metrics=data.get("metrics", {}),
                signature=data.get("signature"),
            )
        except Exception:
            return None

    def save_job(self, job: JobRecord):
        job.updated_at = time.time()
        job_dir = self._get_job_dir(job.job_id)
        status_path = os.path.join(job_dir, "status.json")
        data = asdict(job)
        data["status"] = job.status.value
        with open(status_path, "w") as f:
            json.dump(data, f, indent=2)

    def list_queued_jobs(self) -> List[str]:
        queued_ids = []
        if os.path.exists(self.queue_file):
            with open(self.queue_file, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        jid = entry["job_id"]
                        job = self.get_job(jid)
                        if job and job.status == JobStatus.QUEUED:
                            queued_ids.append(jid)
                    except Exception:
                        pass
        return queued_ids

    def list_jobs(self, limit: int = 50) -> List[JobRecord]:
        jobs = []
        try:
            if not os.path.exists(self.base_dir):
                return []
            candidates = [
                os.path.join(self.base_dir, d)
                for d in os.listdir(self.base_dir)
                if os.path.isdir(os.path.join(self.base_dir, d))
            ]
            for job_dir in candidates:
                status_path = os.path.join(job_dir, "status.json")
                if os.path.exists(status_path):
                    try:
                        with open(status_path, "r") as f:
                            data = json.load(f)
                        job = self.get_job(data["job_id"])
                        if job:
                            jobs.append(job)
                    except Exception:
                        continue
            jobs.sort(key=lambda x: x.updated_at, reverse=True)
            return jobs[:limit]
        except Exception:
            return []


class RedisJobStore(BaseJobStore):
    def __init__(self, redis_url: str, secrets: Dict[str, str]):
        from gateway.app.core.redis_pool import get_redis_client

        # P3b: Clustering Support
        cluster_nodes = secrets.get("REDIS_CLUSTER_NODES", "")
        self.redis = get_redis_client(redis_url, cluster_nodes=cluster_nodes)
        
        if not self.redis:
            # Fallback (standlone legacy)
            import redis
            self.redis = redis.from_url(redis_url, decode_responses=True)
            
        self.queue_key = "jobs:queue"
        self.job_prefix = "jobs:data:"
        self.secrets = secrets

    def submit_job(self, request: JobRequest) -> str:
        job_id = str(uuid.uuid4())
        job = JobRecord(
            job_id=job_id, request=request, status=JobStatus.QUEUED, created_at=time.time(), updated_at=time.time()
        )
        secret = self.secrets.get("NOOGH_JOB_SIGNING_SECRET")
        if secret:
            sign_job_record(job, secret)
            print(f"DEBUG: Signed job {job_id} with secret ending in ...{secret[-4:]} | Sig: {job.signature}")
        else:
            print(f"DEBUG: No signing secret found in RedisJobStore! Keys: {list(self.secrets.keys())}")
        self.save_job(job)
        self.redis.rpush(self.queue_key, job_id)
        return job_id

    def get_job(self, job_id: str) -> Optional[JobRecord]:
        data = self.redis.get(f"{self.job_prefix}{job_id}")
        if not data:
            return None
        try:
            job_dict = json.loads(data)
            budgets_data = job_dict["request"].pop("budgets")
            budgets = JobBudget(**budgets_data)
            request = JobRequest(budgets=budgets, **job_dict["request"])
            return JobRecord(
                job_id=job_dict["job_id"],
                request=request,
                status=JobStatus(job_dict["status"]),
                created_at=job_dict["created_at"],
                updated_at=job_dict["updated_at"],
                result=job_dict.get("result"),
                error=job_dict.get("error"),
                metrics=job_dict.get("metrics", {}),
                signature=job_dict.get("signature"),
            )
        except Exception:
            return None

    def save_job(self, job: JobRecord):
        job.updated_at = time.time()
        key = f"{self.job_prefix}{job.job_id}"
        data = asdict(job)
        data["status"] = job.status.value
        self.redis.set(key, json.dumps(data))

    def list_queued_jobs(self) -> List[str]:
        return self.redis.lrange(self.queue_key, 0, -1)

    def list_jobs(self, limit: int = 50) -> List[JobRecord]:
        cursor = 0
        keys = []
        while True:
            cursor, partial_keys = self.redis.scan(cursor, match=f"{self.job_prefix}*", count=100)
            keys.extend(partial_keys)
            if cursor == 0:
                break
        jobs = []
        for k in keys[:limit]:
            job_id = k.replace(self.job_prefix, "")
            job = self.get_job(job_id)
            if job:
                jobs.append(job)
        jobs.sort(key=lambda x: x.updated_at, reverse=True)
        return jobs[:limit]

    def pop_job(self) -> Optional[str]:
        return self.redis.lpop(self.queue_key)

    def check_health(self) -> bool:
        try:
            return self.redis.ping()
        except Exception:
            return False


def get_job_store(secrets: Dict[str, str]) -> BaseJobStore:
    """Factory with Production Enforcement"""
    redis_url = secrets.get("REDIS_URL")
    data_dir = secrets.get("NOOGH_DATA_DIR")
    is_prod = secrets.get("NOOGH_ENV", "dev").lower() == "production"
    if redis_url:
        return RedisJobStore(redis_url, secrets=secrets)
    if is_prod:
        raise RuntimeError("CRITICAL: Redis is REQUIRED for Production mode. FileJobStore is unsafe.")
    if not data_dir:
        raise RuntimeError("CRITICAL: NOOGH_DATA_DIR is required for FileJobStore")
    return FileJobStore(base_dir=get_job_dir(data_dir))
