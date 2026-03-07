import sqlite3
import os
import json
import logging
import time
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import asdict
from contextlib import closing

logger = logging.getLogger("unified_core.core.memory_store")

class UnifiedMemoryStore:
    """
    SQLite-backed Unified Shared Memory.
    ARCHITECTURE: Async API wrapping a Synchronous Deterministic Core.
    """
    def __init__(self, db_path: str = None):
        if not db_path:
            env_path = os.environ.get("NOOGH_DATA_DIR")
            base_dir = Path(env_path) if env_path else Path(__file__).resolve().parents[3] / "data"
            base_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(base_dir / "shared_memory.sqlite")
        else:
            self.db_path = db_path
            
        self._query_latency_ewma = 0.0 # EWMA for Performance Monitoring
        self._alpha = 0.2              # EWMA Smoothing factor
        
        self._init_db()
        logger.info(f"MemoryStore Initialized (Async API) at {self.db_path}")

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _init_db(self):
        with closing(self._get_connection()) as conn, conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS beliefs (key TEXT PRIMARY KEY, value TEXT, use_count INTEGER DEFAULT 0, last_used_at TIMESTAMP, utility_score REAL DEFAULT 0.5, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
                CREATE TABLE IF NOT EXISTS predictions (key TEXT PRIMARY KEY, value TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
                CREATE TABLE IF NOT EXISTS falsifications (key TEXT PRIMARY KEY, value TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
                CREATE TABLE IF NOT EXISTS observations (key TEXT PRIMARY KEY, value TEXT, timestamp REAL);
                CREATE TABLE IF NOT EXISTS evolutions (evolution_id TEXT PRIMARY KEY, path TEXT, eye TEXT, rationale TEXT, context TEXT, outcome TEXT, success INTEGER, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
                CREATE TABLE IF NOT EXISTS experiences (experience_id TEXT PRIMARY KEY, context TEXT, action TEXT, outcome TEXT, success INTEGER, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
                CREATE INDEX IF NOT EXISTS idx_obs_ts ON observations(timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_evol_ts ON evolutions(timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_exp_ts ON experiences(timestamp DESC);
            """)

    def _serialize(self, obj: Any) -> str:
        if obj is None: return json.dumps(None)
        if hasattr(obj, "to_dict"): return json.dumps(obj.to_dict())
        
        # Check if it's a dataclass
        try:
            from dataclasses import is_dataclass, asdict
            if is_dataclass(obj):
                return json.dumps(asdict(obj))
        except ImportError:
            pass

        if isinstance(obj, (str, int, float, bool, list, dict)): 
            return json.dumps(obj)
            
        return json.dumps(str(obj))

    def _sync_op(func):
        """Internal decorator for sync ops to handle retries."""
        def wrapper(self, *args, **kwargs):
            for i in range(5):
                try: return func(self, *args, **kwargs)
                except sqlite3.OperationalError as e:
                    if "locked" in str(e) or "busy" in str(e):
                        time.sleep(0.05 * (2**i))
                        continue
                    raise
        return wrapper

    # --- ASYNC PUBLIC API ---

    async def set_belief(self, key: str, value: Any, utility: float = 0.5):
        return await asyncio.to_thread(self._set_belief_sync, key, value, utility)

    async def get_belief(self, key: str) -> Optional[Dict[str, Any]]:
        return await asyncio.to_thread(self._get_belief_sync, key)

    async def get_all_beliefs(self) -> Dict[str, Any]:
        return await asyncio.to_thread(self._get_all_beliefs_sync)

    async def save_prediction(self, prediction: Any):
        return await asyncio.to_thread(self._save_prediction_sync, prediction)

    async def get_prediction(self, key: str) -> Optional[Dict[str, Any]]:
        return await asyncio.to_thread(self._get_prediction_sync, key)

    async def get_all_predictions(self) -> Dict[str, Any]:
        return await asyncio.to_thread(self._get_all_predictions_sync)

    async def append_observation(self, observation: Any):
        return await asyncio.to_thread(self._append_observation_sync, observation)

    async def get_recent_observations(self, limit: int = 100) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self._get_recent_observations_sync, limit)

    async def append_falsification(self, falsification: Any):
        return await asyncio.to_thread(self._append_falsification_sync, falsification)

    async def get_all_falsifications(self) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self._get_all_falsifications_sync)

    async def update_beliefs_by_observation(self, observation_id: str, pattern: str, delta: float):
        return await asyncio.to_thread(self._update_beliefs_sync, pattern, delta)

    async def delete_belief(self, key: str):
        return await asyncio.to_thread(self._delete_belief_sync, key)

    async def record_evolution_step(self, evolution_id: str, path: str, eye: str, rationale: str, context: Optional[Dict], outcome: str, success: bool):
        return await asyncio.to_thread(self._record_evolution_step_sync, evolution_id, path, eye, rationale, context, outcome, success)

    async def record_experience(self, experience_id: str, context: str, action: str, outcome: str, success: bool):
        return await asyncio.to_thread(self._record_experience_sync, experience_id, context, action, outcome, success)

    async def get_evolution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self._get_evolution_history_sync, limit)

    async def health_check(self) -> Dict[str, Any]:
        return await asyncio.to_thread(self._health_check_sync)

    # --- SYNC INTERNAL OPS ---

    @_sync_op
    def _set_belief_sync(self, key: str, value: Any, utility: float):
        serialized = self._serialize(value)
        with closing(self._get_connection()) as conn, conn:
            conn.execute("INSERT INTO beliefs (key, value, utility_score) VALUES (?, ?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, utility_score=excluded.utility_score, updated_at=CURRENT_TIMESTAMP", (key, serialized, utility))

    @_sync_op
    def _get_belief_sync(self, key: str) -> Optional[Dict[str, Any]]:
        with closing(self._get_connection()) as conn, conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM beliefs WHERE key = ?", (key,))
            row = cursor.fetchone()
            if not row: return None
            data = json.loads(row[0])
            return data if isinstance(data, dict) else {"proposition": str(data), "confidence": 0.5, "state": "active"}

    @_sync_op
    def _get_all_beliefs_sync(self) -> Dict[str, Any]:
        with closing(self._get_connection()) as conn, conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM beliefs")
            return {r[0]: (json.loads(r[1]) if isinstance(json.loads(r[1]), dict) else {"prop": str(r[1])}) for r in cursor.fetchall()}

    @_sync_op
    def _save_prediction_sync(self, prediction: Any):
        serialized = self._serialize(prediction)
        pk = getattr(prediction, "prediction_id", None) or (prediction.get("prediction_id") if isinstance(prediction, dict) else str(hash(serialized)))
        with closing(self._get_connection()) as conn, conn:
            conn.execute("INSERT INTO predictions (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (pk, serialized))

    @_sync_op
    def _get_prediction_sync(self, key: str) -> Optional[Dict[str, Any]]:
        with closing(self._get_connection()) as conn, conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM predictions WHERE key = ?", (key,))
            row = cursor.fetchone()
            return json.loads(row[0]) if row else None

    @_sync_op
    def _get_all_predictions_sync(self) -> Dict[str, Any]:
        with closing(self._get_connection()) as conn, conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM predictions")
            results = {}
            for r in cursor.fetchall():
                data = json.loads(r[0])
                pk = data.get("prediction_id", "unknown_" + str(time.time()))
                results[pk] = data
            return results

    @_sync_op
    def _append_observation_sync(self, observation: Any):
        serialized = self._serialize(observation)
        ok = getattr(observation, "observation_id", None) or observation.get("observation_id", "obs_" + str(time.time()))
        ts = getattr(observation, "timestamp", time.time())
        with closing(self._get_connection()) as conn, conn:
            conn.execute("INSERT INTO observations (key, value, timestamp) VALUES (?, ?, ?)", (ok, serialized, ts))
    @_sync_op
    def _delete_belief_sync(self, key: str):
        with closing(self._get_connection()) as conn, conn:
            conn.execute("DELETE FROM beliefs WHERE key = ?", (key,))

    @_sync_op
    def _health_check_sync(self) -> Dict[str, Any]:
        try:
            with closing(self._get_connection()) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT count(*) FROM beliefs")
                count = cursor.fetchone()[0]
                return {"status": "healthy", "count": count, "db_path": self.db_path}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    @_sync_op
    def _get_recent_observations_sync(self, limit: int) -> List[Dict[str, Any]]:
        with closing(self._get_connection()) as conn, conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM observations ORDER BY timestamp DESC LIMIT ?", (limit,))
            return [json.loads(r[0]) for r in cursor.fetchall()]

    @_sync_op
    def _append_falsification_sync(self, falsification: Any):
        serialized = self._serialize(falsification)
        fk = getattr(falsification, "falsification_id", None) or falsification.get("falsification_id", "fals_" + str(time.time()))
        with closing(self._get_connection()) as conn, conn:
            conn.execute("INSERT INTO falsifications (key, value) VALUES (?, ?)", (fk, serialized))

    @_sync_op
    def _get_all_falsifications_sync(self) -> List[Dict[str, Any]]:
        with closing(self._get_connection()) as conn, conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM falsifications")
            return [json.loads(r[0]) for r in cursor.fetchall()]

    @_sync_op
    def _update_beliefs_sync(self, pattern: str, delta: float):
        with closing(self._get_connection()) as conn, conn:
            conn.execute("UPDATE beliefs SET utility_score = MIN(1.0, utility_score + ?) WHERE value LIKE ?", (delta, f"%{pattern}%"))

    @_sync_op
    def _record_evolution_step_sync(self, evolution_id: str, path: str, eye: str, rationale: str, context: Optional[Dict], outcome: str, success: bool):
        ctx_serialized = self._serialize(context) if context else "{}"
        with closing(self._get_connection()) as conn, conn:
            conn.execute(
                "INSERT INTO evolutions (evolution_id, path, eye, rationale, context, outcome, success) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (evolution_id, path, eye, rationale, ctx_serialized, outcome, int(success))
            )

    @_sync_op
    def _get_evolution_history_sync(self, limit: int) -> List[Dict[str, Any]]:
        with closing(self._get_connection()) as conn, conn:
            cursor = conn.cursor()
            cursor.execute("SELECT evolution_id, path, eye, rationale, context, outcome, success, timestamp FROM evolutions ORDER BY timestamp DESC LIMIT ?", (limit,))
            results = []
            for r in cursor.fetchall():
                results.append({
                    "evolution_id": r[0], "path": r[1], "eye": r[2],
                    "rationale": r[3], "context": json.loads(r[4]),
                    "outcome": r[5], "success": bool(r[6]), "timestamp": r[7]
                })
            return results

    @_sync_op
    def _record_experience_sync(self, experience_id: str, context: str, action: str, outcome: str, success: bool):
        with closing(self._get_connection()) as conn, conn:
            conn.execute(
                "INSERT INTO experiences (experience_id, context, action, outcome, success) VALUES (?, ?, ?, ?, ?)",
                (experience_id, context, action, outcome, int(success))
            )
