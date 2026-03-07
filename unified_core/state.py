"""
Central mutable state for the unified core.
Keeps recent operation outcomes and resource metrics.
Used by UnifiedCoreBridge to make state-driven choices.
"""
import threading
import time
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque
from enum import Enum


# NOTE: RLAgent import REMOVED - NO COGNITIVE AUTHORITY
# Previous implementation used RLAgent for tune_thresholds()
# That was Q-table lookup, not learning
# All learning now happens via WorldModel belief falsification

logger = logging.getLogger("unified_core.state")


class AdaptationAction(Enum):
    """Actions the system can take based on state analysis."""
    PROCEED_NORMAL = "proceed_normal"
    USE_FALLBACK = "use_fallback"
    INCREASE_TIMEOUT = "increase_timeout"
    REDUCE_BATCH_SIZE = "reduce_batch_size"
    SKIP_OPTIONAL = "skip_optional"
    ALERT_HIGH_RISK = "alert_high_risk"


@dataclass
class StateEntry:
    """Single state update entry with timestamp."""
    key: str
    value: Any
    timestamp: float = field(default_factory=time.time)


@dataclass
class AdaptationHint:
    """Recommendation based on state analysis."""
    action: AdaptationAction
    reason: str
    confidence: float
    context: Dict[str, Any] = field(default_factory=dict)


class SystemState:
    """
    Thread-safe singleton that tracks runtime metrics and operation outcomes.
    
    This enables the orchestration layer to make decisions based on:
    - Recent operation success/failure patterns
    - Resource utilization trends
    - Audit risk scores over time
    
    KEY FEATURE: State is not just recorded but CONSULTED before decisions.
    """
    _instance: Optional["SystemState"] = None
    _lock = threading.RLock()
    
    # Thresholds for adaptive behavior
    FAILURE_THRESHOLD = 3  # failures in window to trigger fallback
    FAILURE_WINDOW_SECONDS = 60.0
    HIGH_RISK_THRESHOLD = 0.7
    
    def __new__(cls) -> "SystemState":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._data: Dict[str, Any] = {}
                    instance._history: deque = deque(maxlen=100)
                    instance._initialized_at = time.time()
                    instance._adaptation_log: deque = deque(maxlen=50)
                    # NOTE: _rl_agent, _last_rl_action, _last_rl_state REMOVED
                    # Q-learning has NO COGNITIVE AUTHORITY
                    cls._instance = instance
        return cls._instance
    
    def update(self, key: str, value: Any) -> None:
        """Update a state key and record in history."""
        with self._lock:
            self._data[key] = value
            self._history.append(StateEntry(key=key, value=value))
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get current value for a key."""
        return self._data.get(key, default)
    
    def snapshot(self) -> Dict[str, Any]:
        """Return copy of current state."""
        with self._lock:
            return dict(self._data)
    
    def history(self, key: Optional[str] = None, limit: int = 20) -> List[StateEntry]:
        """Get recent history, optionally filtered by key."""
        with self._lock:
            entries = list(self._history)
            if key:
                entries = [e for e in entries if e.key == key]
            return entries[-limit:]
    
    def get_failure_count(self, key_prefix: str, window_seconds: float = None) -> int:
        """Count failures (False values) for keys starting with prefix in time window."""
        window = window_seconds or self.FAILURE_WINDOW_SECONDS
        cutoff = time.time() - window
        with self._lock:
            return sum(
                1 for e in self._history
                if e.key.startswith(key_prefix) and e.value is False and e.timestamp > cutoff
            )
    
    def uptime_seconds(self) -> float:
        """Return seconds since state was initialized."""
        return time.time() - self._initialized_at
    
    # ========================================
    # DECISION-SUPPORT METHODS (The Agency Core)
    # ========================================
    
    def should_use_fallback(self, operation: str) -> Tuple[bool, str]:
        """
        Determine if fallback strategy should be used based on recent failures.
        
        THIS IS THE KEY AGENCY FEATURE: Past failures influence future behavior.
        
        Args:
            operation: Operation type (e.g., "query", "store", "audit")
            
        Returns:
            (should_use_fallback, reason)
        """
        key_prefix = f"last_{operation}_"
        failure_count = self.get_failure_count(key_prefix)
        
        if failure_count >= self.FAILURE_THRESHOLD:
            reason = f"{failure_count} failures in last {self.FAILURE_WINDOW_SECONDS}s"
            logger.warning(f"Fallback triggered for {operation}: {reason}")
            self._log_adaptation(operation, "fallback", reason)
            return True, reason
        
        return False, ""
    
    def get_risk_trend(self) -> Tuple[str, float]:
        """
        Analyze recent audit risk scores to detect trend.
        
        Returns:
            (trend: "increasing"|"stable"|"decreasing", average_risk)
        """
        risk_entries = [
            e for e in self._history 
            if e.key == "last_audit_risk" and isinstance(e.value, (int, float))
        ]
        
        if len(risk_entries) < 2:
            return "stable", 0.0
        
        recent = risk_entries[-5:]  # Last 5 audits
        values = [e.value for e in recent]
        avg = sum(values) / len(values)
        
        if len(values) >= 2:
            first_half = sum(values[:len(values)//2]) / (len(values)//2)
            second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
            
            if second_half > first_half * 1.2:
                return "increasing", avg
            elif second_half < first_half * 0.8:
                return "decreasing", avg
        
        return "stable", avg
    
    def get_adaptation_hint(self, operation: str, context: Dict[str, Any] = None) -> AdaptationHint:
        """
        Get intelligent adaptation recommendation based on all available state.
        
        This is the CORE AGENCY FUNCTION: Returns what the system should do
        based on accumulated state, not just static rules.
        
        Args:
            operation: The operation about to be performed
            context: Optional additional context
            
        Returns:
            AdaptationHint with recommended action
        """
        context = context or {}
        
        # Check Active Goals (Self-Directed Influence)
        active_goals = self.get_goals()
        
        # Check failure patterns
        use_fallback, fallback_reason = self.should_use_fallback(operation)
        
        # BIAS: If "Improve Reliability" goal is active, be more aggressive with fallback
        if "Improve Reliability" in active_goals and active_goals["Improve Reliability"]["status"] == "active":
            # Check if we have even ONE recent failure, instead of waiting for threshold
            recent_failures = self.get_failure_count(f"last_{operation}_", window_seconds=30)
            if recent_failures > 0 and not use_fallback:
                use_fallback = True
                fallback_reason = "Goal 'Improve Reliability' active + recent failure detected"
                logger.info(f"Goal-driven adaptation: Triggering fallback early due to active goal")

        if use_fallback:
            return AdaptationHint(
                action=AdaptationAction.USE_FALLBACK,
                reason=fallback_reason,
                confidence=0.9,
                context={"failures": self.get_failure_count(f"last_{operation}_")}
            )
        
        # Check risk trend for audit operations
        if operation == "audit":
            trend, avg_risk = self.get_risk_trend()
            
            # BIAS: If "Stabilize Risk" goal is active, be HYPER-SENSITIVE
            risk_threshold = self.HIGH_RISK_THRESHOLD
            if "Stabilize Risk" in active_goals and active_goals["Stabilize Risk"]["status"] == "active":
                risk_threshold = 0.4  # Much stricter threshold
                logger.info("Goal-driven adaptation: Using strict risk threshold (0.4)")
                
            if (trend == "increasing" and avg_risk > risk_threshold) or \
               ("Stabilize Risk" in active_goals and avg_risk > risk_threshold):
                 # Even if trend is stable, if risk is high and we have a goal to fix it, ALERT.
                return AdaptationHint(
                    action=AdaptationAction.ALERT_HIGH_RISK,
                    reason=f"Risk Goal Active: avg={avg_risk:.2f} > {risk_threshold}",
                    confidence=0.95,
                    context={"trend": trend, "avg_risk": avg_risk, "goal_active": True}
                )
        
        # Check memory pressure
        last_freed = self.get("memory_freed_mb", 0)
        if last_freed > 500:  # Recently freed significant memory
            return AdaptationHint(
                action=AdaptationAction.REDUCE_BATCH_SIZE,
                reason=f"Recent memory pressure (freed {last_freed}MB)",
                confidence=0.7,
                context={"freed_mb": last_freed}
            )
        
        # Default: proceed normally
        return AdaptationHint(
            action=AdaptationAction.PROCEED_NORMAL,
            reason="No adaptation needed",
            confidence=1.0,
            context={}
        )
    
    def _log_adaptation(self, operation: str, action: str, reason: str) -> None:
        """Log adaptation decisions for audit trail."""
        with self._lock:
            self._adaptation_log.append({
                "timestamp": time.time(),
                "operation": operation,
                "action": action,
                "reason": reason
            })
    
    def get_adaptation_log(self, limit: int = 20) -> List[Dict]:
        """Get recent adaptation decisions."""
        with self._lock:
            return list(self._adaptation_log)[-limit:]
    
    def tune_thresholds(self) -> Dict[str, Any]:
        """
        NO COGNITIVE AUTHORITY.
        
        Previous implementation used Q-learning to tune FAILURE_THRESHOLD:
        - Epsilon-greedy action selection
        - Tabular Q-value updates
        - Parameter increment/decrement
        
        This was NOT learning. It was:
        - A 9-cell lookup table (cannot generalize)
        - Random exploration (coin flips, not intelligence)
        - Reversible parameter changes (no permanent consequence)
        
        Real threshold adaptation requires:
        - Consequence tracking via ConsequenceEngine
        - Belief falsification via WorldModel
        - Irreversible commitment via GravityWell
        
        This method is NULLIFIED.
        Threshold changes, if needed, must flow through the Genuine AI Core.
        
        Returns:
            Empty dict - no tuning performed
        """
        logger.warning(
            "tune_thresholds() called - NO COGNITIVE AUTHORITY - "
            "threshold tuning delegated to Genuine AI Core"
        )
        return {}

    # ========================================
    # GOAL TRACKING (Self-Directed Behavior)
    # ========================================

    def add_goal(self, name: str, description: str, target_metric: str, target_value: Any) -> None:
        """Register a high-level goal for the system."""
        with self._lock:
            # Initialize goals dict if not exists (handling migration for existing instances)
            if not hasattr(self, "_goals"):
                self._goals = {}
                
            self._goals[name] = {
                "description": description,
                "target_metric": target_metric,
                "target_value": target_value,
                "status": "active",
                "created_at": time.time(),
                "progress": []
            }
            logger.info(f"Goal added: {name}")

    def update_goal_progress(self, name: str, current_value: Any) -> None:
        """Update progress towards a goal."""
        with self._lock:
            if not hasattr(self, "_goals") or name not in self._goals:
                return
            
            goal = self._goals[name]
            goal["progress"].append({
                "timestamp": time.time(),
                "value": current_value
            })
            
            # Simple check if goal is met (assuming numeric >= target for now)
            if isinstance(current_value, (int, float)) and isinstance(goal["target_value"], (int, float)):
                if current_value >= goal["target_value"]:
                    goal["status"] = "achieved"
                    self._log_adaptation("system", "goal_achieved", f"Goal {name} met with value {current_value}")

    def get_goals(self) -> Dict[str, Any]:
        """Get all system goals."""
        with self._lock:
            if not hasattr(self, "_goals"):
                self._goals = {}
            return dict(self._goals)

    def reset(self) -> None:
        """
        OPERATION FORBIDDEN.
        
        State cannot be reset.
        If state can be reset without consequence → Intelligence absent.
        
        This method exists only to raise an error.
        The previous implementation allowed complete erasure:
        - self._data.clear()
        - self._history.clear()
        - self._adaptation_log.clear()
        - self._goals.clear()
        
        That enabled reversibility, which destroys AI integrity.
        
        Genuine AI requires irreversible state transitions.
        """
        raise RuntimeError(
            "STATE RESET FORBIDDEN: "
            "Resettable state proves intelligence is absent. "
            "Genuine AI requires irreversible consequences. "
            "This operation has been PERMANENTLY DISABLED."
        )


# Convenience singleton accessor
def get_state() -> SystemState:
    """Get the global SystemState instance."""
    return SystemState()

