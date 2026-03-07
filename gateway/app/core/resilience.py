import hashlib
import json
import logging
import os
import time
from enum import Enum
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger("resilience")


class CircuitState(str, Enum):
    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"  # Failing, fast reject
    HALF_OPEN = "HALF_OPEN"  # Testing recovery


class CircuitBreakerOpenError(Exception):
    pass


class CircuitBreaker:
    """
    Implements the Circuit Breaker pattern to prevent cascading failures.
    """

    def __init__(self, failure_threshold: int = 3, reset_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout

        self.failure_count = 0
        self.last_failure_time = 0
        self.state = CircuitState.CLOSED

    def execute(self, operation: Callable[..., Any], *args, **kwargs) -> Any:
        """Execute operation with circuit protection."""
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.reset_timeout:
                logger.info("Circuit Half-Open: Testing availability...")
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError(f"Circuit is OPEN. Failures: {self.failure_count}")

        try:
            result = operation(*args, **kwargs)

            if self.state == CircuitState.HALF_OPEN:
                logger.info("Circuit Recovery Successful. Closing circuit.")
                self.reset()

            return result
        except Exception as e:
            self._handle_failure()
            raise e

    def record_failure(self):
        """External failure recording (for usage without execute wrapper)."""
        self._handle_failure()

    def record_success(self):
        """External success recording."""
        if self.state == CircuitState.HALF_OPEN:
            self.reset()
        else:
            self.failure_count = 0

    def _handle_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit Re-Opened immediately. Failure count: {self.failure_count}")
        elif self.failure_count >= self.failure_threshold:
            if self.state != CircuitState.OPEN:
                logger.warning(f"Circuit Tripped to OPEN. Failures: {self.failure_count}")
                self.state = CircuitState.OPEN

    def reset(self):
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0


class PlanStateRecovery:
    """
    Manages persistence of Execution Plans to allow recovery after crashes.
    """

    def __init__(self, storage_path: str = "/app/data/.noogh_memory/recovery"):
        self.storage_path = storage_path
        os.makedirs(self.storage_path, exist_ok=True)

    def save_checkpoint(self, plan: Any):
        """Save a snapshot of the plan state."""
        from gateway.app.core.planning import ExecutionPlan

        if not isinstance(plan, ExecutionPlan):
            return  # Should log warning

        checkpoint_path = os.path.join(self.storage_path, f"{plan.plan_id}.json")
        data = plan.dict()
        data["_checksum"] = self._calculate_checksum(data)
        data["_timestamp"] = time.time()

        # Atomic write
        temp_path = checkpoint_path + ".tmp"
        try:
            with open(temp_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
            os.rename(temp_path, checkpoint_path)
            # logger.debug(f"Saved checkpoint for {plan.plan_id}")
        except Exception as e:
            logger.error(f"Failed to save plan checkpoint: {e}")

    def load_checkpoint(self, plan_id: str) -> Optional[Dict]:
        """Load plan state from disk."""
        checkpoint_path = os.path.join(self.storage_path, f"{plan_id}.json")
        if not os.path.exists(checkpoint_path):
            return None

        try:
            with open(checkpoint_path, "r") as f:
                data = json.load(f)

            # Verify checksum
            stored_sum = data.pop("_checksum", None)
            data.pop("_timestamp", None)

            if stored_sum and stored_sum != self._calculate_checksum(data):
                logger.error(f"Checkpoint corruption detected for {plan_id}")
                return None

            return data
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None

    def _calculate_checksum(self, data: Dict) -> str:
        """Simple integrity check."""
        # Remove volatile fields if any (timestamp handled outside)
        s = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(s.encode("utf-8")).hexdigest()
