import os
import sqlite3
from datetime import datetime
from typing import Any, Dict


class AnalyticsStore:
    """Stores historical job performance metrics."""

    def __init__(self, db_path: str):
        if not db_path:
            raise ValueError("db_path is required for AnalyticsStore")
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS job_metrics (
                    id TEXT PRIMARY KEY,
                    job_type TEXT,
                    steps INTEGER,
                    duration_ms REAL,
                    status TEXT,
                    timestamp DATETIME
                )
            """
            )

    def log_job(self, job_id: str, job_type: str, steps: int, duration_ms: float, status: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO job_metrics VALUES (?, ?, ?, ?, ?, ?)",
                (job_id, job_type, steps, duration_ms, status, datetime.now()),
            )

    def predict_cost(self, job_type: str) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT AVG(steps), AVG(duration_ms), COUNT(*) 
                FROM job_metrics 
                WHERE job_type = ? AND status = 'SUCCEEDED'
            """,
                (job_type,),
            )
            row = cursor.fetchone()

            if row and row[2] > 0:
                avg_steps = round(row[0] or 0, 1)
                avg_time = round(row[1] or 0, 0)
                count = row[2]
                confidence = "High" if count > 10 else "Low"
            else:
                avg_steps = 5
                avg_time = 30000
                count = 0
                confidence = "None (Heuristic)"

            return {
                "estimated_steps": avg_steps,
                "estimated_duration_ms": avg_time,
                "sample_size": count,
                "confidence": confidence,
            }

    def get_system_stats(self) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*), AVG(duration_ms) FROM job_metrics")
            row = cursor.fetchone()
            return {"total_jobs_tracked": row[0], "avg_system_latency": round(row[1] or 0, 2)}


def get_analytics(data_dir: str) -> AnalyticsStore:
    if not data_dir:
        raise ValueError("data_dir is required for AnalyticsStore")
    db_path = os.path.join(data_dir, ".noogh_memory", "analytics.db")
    return AnalyticsStore(db_path=db_path)
