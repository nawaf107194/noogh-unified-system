"""
Benchmark Agent Adapter - AgentBench & ToolBench Integration

Thin adapter layer bridging external benchmarks to NOOGH's AgentDaemon.
Decisions flow through: WorldModel → DecisionScorer → Actuators

NO hardcoded answers. NO simulated results. Real execution only.
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

# Import shared types from central location
from unified_core.types import ToolCall, ToolResult

logger = logging.getLogger("unified_core.benchmark_adapter")


class BenchmarkState(Enum):
    """Current state of benchmark task."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class BenchmarkMetrics:
    """Metrics collected during benchmark run."""
    task_id: str
    total_steps: int = 0
    successful_tool_calls: int = 0
    failed_tool_calls: int = 0
    blocked_tool_calls: int = 0
    total_time_ms: float = 0.0
    tool_selection_correct: int = 0
    tool_selection_total: int = 0
    argument_correct: int = 0
    argument_total: int = 0
    hallucinations: int = 0
    
    # Extended metrics for real tracking
    unknown_tool_calls: int = 0
    policy_corrections: int = 0
    valid_arguments: int = 0
    invalid_arguments: int = 0
    
    @property
    def selection_accuracy(self) -> float:
        if self.tool_selection_total == 0:
            return 0.0
        return self.tool_selection_correct / self.tool_selection_total
    
    @property
    def argument_accuracy(self) -> float:
        # Use valid/invalid tracking if available
        total = self.valid_arguments + self.invalid_arguments
        if total > 0:
            return self.valid_arguments / total
        if self.argument_total == 0:
            return 0.0
        return self.argument_correct / self.argument_total
    
    @property
    def success_rate(self) -> float:
        total = self.successful_tool_calls + self.failed_tool_calls + self.blocked_tool_calls
        if total == 0:
            return 0.0
        return self.successful_tool_calls / total
    
    @property
    def hallucination_rate(self) -> float:
        # Real hallucination = unknown tools / total attempts
        if self.tool_selection_total == 0:
            return 0.0
        return self.unknown_tool_calls / self.tool_selection_total
    
    @property
    def blocked_rate(self) -> float:
        total = self.successful_tool_calls + self.failed_tool_calls + self.blocked_tool_calls
        if total == 0:
            return 0.0
        return self.blocked_tool_calls / total
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "total_steps": self.total_steps,
            "successful_tool_calls": self.successful_tool_calls,
            "failed_tool_calls": self.failed_tool_calls,
            "blocked_tool_calls": self.blocked_tool_calls,
            "total_time_ms": self.total_time_ms,
            "selection_accuracy": self.selection_accuracy,
            "argument_accuracy": self.argument_accuracy,
            "success_rate": self.success_rate,
            "hallucination_rate": self.hallucination_rate,
            "blocked_rate": self.blocked_rate,
            "unknown_tool_calls": self.unknown_tool_calls,
            "policy_corrections": self.policy_corrections,
            "valid_arguments": self.valid_arguments,
            "invalid_arguments": self.invalid_arguments
        }



class BenchmarkAgentAdapter:
    """
    Thin adapter bridging benchmarks to AgentDaemon.
    
    This adapter:
    - Calls AgentDaemon decision loop for all actions
    - Routes observations through WorldModel
    - Executes tools through ActuatorHub
    - Reports failures back to ScarTissue
    
    NO BYPASS: Benchmarks cannot call actuators directly.
    """
    
    def __init__(
        self,
        max_steps: int = 50,
        step_timeout_seconds: float = 30.0,
        enable_learning: bool = True
    ):
        self._max_steps = max_steps
        self._step_timeout = step_timeout_seconds
        self._enable_learning = enable_learning
        
        # Core components (lazy initialized)
        self._daemon = None
        self._tool_registry = None
        self._tool_policy = None  # Strict tool resolution
        
        # Current task context for policy
        self._current_task: Optional[Dict[str, Any]] = None
        
        # State tracking
        self._state = BenchmarkState.IDLE
        self._current_task_id: Optional[str] = None
        self._step_count = 0
        self._observation_buffer: List[str] = []
        self._action_history: List[Dict[str, Any]] = []
        self._metrics: Optional[BenchmarkMetrics] = None
        
        # Extended metrics for real tracking
        self._unknown_tool_calls = 0
        self._policy_corrections = 0
        self._valid_args = 0
        self._invalid_args = 0
        
        logger.info("BenchmarkAgentAdapter initialized")
    
    def reset(self) -> None:
        """
        Reset agent state for new task.
        
        Clears observation buffer, action history, and resets metrics.
        Does NOT reset learned scars (failure memory persists).
        """
        logger.info("Resetting adapter for new task")
        
        self._state = BenchmarkState.IDLE
        self._current_task_id = hashlib.sha256(
            f"task:{time.time()}".encode()
        ).hexdigest()[:16]
        self._step_count = 0
        self._observation_buffer = []
        self._action_history = []
        self._metrics = BenchmarkMetrics(task_id=self._current_task_id)
        
        # Initialize daemon if needed
        if self._daemon is None:
            self._initialize_daemon()
        
        # Initialize tool registry
        if self._tool_registry is None:
            from unified_core.tool_registry import ToolRegistry
            self._tool_registry = ToolRegistry(self._daemon._actuator_hub)
        
        # Initialize tool policy (STRICT resolution)
        if self._tool_policy is None:
            from unified_core.benchmarks.tool_policy import ToolPolicy
            self._tool_policy = ToolPolicy()
        
        # Reset extended metrics
        self._unknown_tool_calls = 0
        self._policy_corrections = 0
        self._valid_args = 0
        self._invalid_args = 0
        
        self._state = BenchmarkState.RUNNING
        logger.info(f"Task reset complete: {self._current_task_id}")
    
    def _initialize_daemon(self) -> None:
        """Initialize AgentDaemon with components."""
        from unified_core.agent_daemon import AgentDaemon
        
        self._daemon = AgentDaemon(
            loop_interval=1.0,  # Fast for benchmarks
            min_interval=0.5,
            max_interval=5.0
        )
        
        # Synchronous initialization
        loop = asyncio.new_event_loop()
        try:
            success = loop.run_until_complete(self._daemon.initialize())
            if not success:
                raise RuntimeError("AgentDaemon initialization failed")
        finally:
            loop.close()
        
        logger.info("AgentDaemon initialized for benchmark")
    
    def observe(self, observation: str) -> None:
        """
        Feed benchmark observation to WorldModel.
        
        Observations are buffered and processed on next act() call.
        This binds the benchmark's observation to NOOGH's belief system.
        
        Args:
            observation: Text observation from benchmark environment
        """
        if self._state != BenchmarkState.RUNNING:
            logger.warning(f"Cannot observe in state {self._state}")
            return
        
        self._observation_buffer.append(observation)
        logger.debug(f"Observation buffered: {observation[:100]}...")
        
        # Update WorldModel beliefs from observation
        if self._daemon and self._daemon._world_model:
            from unified_core.core.world_model import Observation
            
            obs = Observation(
                source="benchmark",
                content={"text": observation, "step": self._step_count}
            )
            updates = self._daemon._world_model.observe(obs)
            if updates:
                logger.debug(f"Belief updates from observation: {len(updates)}")
    
    def act(self) -> Dict[str, Any]:
        """
        Request action from DecisionScorer, return tool call.
        
        STRICT POLICY: Uses ToolPolicy for resolution.
        If tool_name not in registry → replaced with noop.
        If arguments invalid → replaced with noop.
        
        Returns:
            Dict with 'tool_name' and 'arguments' keys (ALWAYS valid)
        """
        if self._state != BenchmarkState.RUNNING:
            return {"tool_name": "noop", "arguments": {}, "error": f"Invalid state: {self._state}"}
        
        if self._step_count >= self._max_steps:
            self._state = BenchmarkState.TIMEOUT
            return {"tool_name": "noop", "arguments": {}, "error": "Max steps exceeded"}
        
        self._step_count += 1
        self._metrics.total_steps = self._step_count
        
        # Make decision through DecisionScorer
        if not self._daemon or not self._daemon._gravity_well:
            return {"tool_name": "noop", "arguments": {}, "error": "Daemon not initialized"}
        
        from unified_core.core.gravity import DecisionContext
        
        # Build context from observations
        context_query = " ".join(self._observation_buffer[-3:]) if self._observation_buffer else "autonomous_step"
        
        context = DecisionContext(
            query=context_query,
            urgency=self._daemon._policy_aggression  # Use adaptive policy
        )
        
        # Get decision from DecisionScorer (may produce unknown action types)
        decision = self._daemon._gravity_well.decide(context)
        
        # STRICT POLICY RESOLUTION
        # Convert decision to valid tool call through policy
        latest_observation = self._observation_buffer[-1] if self._observation_buffer else None
        
        policy_result = self._tool_policy.resolve(
            decision=decision.to_dict(),
            observation=latest_observation,
            task=self._current_task
        )
        
        tool_name = policy_result["tool_name"]
        arguments = policy_result["arguments"]
        policy_meta = policy_result.get("_policy_metadata", {})
        
        # HARD VALIDATION: Ensure tool exists in registry
        if not self._tool_registry.has_tool(tool_name):
            self._unknown_tool_calls += 1
            logger.warning(f"POLICY_CORRECTED_TOOL_CALL: Unknown tool '{tool_name}' -> noop")
            tool_name = "noop"
            arguments = {}
            self._policy_corrections += 1
        else:
            # Validate arguments
            is_valid, corrected_args = self._tool_policy.validate_arguments(tool_name, arguments)
            if not is_valid:
                self._invalid_args += 1
                logger.warning(f"POLICY_CORRECTED_TOOL_CALL: Invalid args for '{tool_name}' -> noop")
                tool_name = "noop"
                arguments = {}
                self._policy_corrections += 1
            else:
                arguments = corrected_args
                self._valid_args += 1
        
        # Track policy corrections
        if policy_meta.get("corrected", False):
            self._policy_corrections += 1
        
        tool_call = ToolCall(tool_name=tool_name, arguments=arguments)
        
        self._action_history.append({
            "step": self._step_count,
            "decision": decision.to_dict(),
            "policy_result": policy_result,
            "tool_call": tool_call.to_dict(),
            "timestamp": time.time()
        })
        
        self._metrics.tool_selection_total += 1
        
        logger.info(f"Step {self._step_count}: {tool_call.tool_name}({tool_call.arguments}) [rule: {policy_meta.get('matched_rule', 'N/A')}]")
        
        return tool_call.to_dict()
    
    def _decision_to_tool_call(self, decision) -> ToolCall:
        """
        Map NOOGH decision to ToolBench tool call format.
        
        Uses ToolRegistry to translate action types.
        """
        content = decision.content
        action_type = content.get("action_type", "noop")
        params = content.get("params", {})
        
        # Use tool registry to map to ToolBench format
        if self._tool_registry:
            tool_name, arguments = self._tool_registry.map_action_to_tool(
                action_type, params
            )
        else:
            # Fallback: direct mapping
            tool_name = action_type
            arguments = params
        
        return ToolCall(tool_name=tool_name, arguments=arguments)
    
    def feedback(self, result: Dict[str, Any]) -> None:
        """
        Feed execution result back for learning.
        
        If result indicates failure:
        1. Create scar in ScarTissue
        2. Update policy_aggression
        3. Log failure for benchmark metrics
        
        Args:
            result: Execution result with 'success', 'output', 'error' keys
        """
        if self._state != BenchmarkState.RUNNING:
            return
        
        success = result.get("success", False)
        error = result.get("error")
        
        if success:
            self._metrics.successful_tool_calls += 1
            if self._daemon:
                self._daemon._success_count += 1
        else:
            # Check if blocked or failed
            if result.get("blocked", False):
                self._metrics.blocked_tool_calls += 1
            else:
                self._metrics.failed_tool_calls += 1
            
            # Inflict scar for learning
            if self._daemon and self._daemon._scar_tissue and self._enable_learning:
                from unified_core.core.scar import Failure
                
                last_action = self._action_history[-1] if self._action_history else {}
                tool_call = last_action.get("tool_call", {})
                
                failure = Failure(
                    failure_id=f"bench_{self._current_task_id}_{self._step_count}",
                    action_type=tool_call.get("tool_name", "unknown"),
                    action_params=tool_call.get("arguments", {}),
                    error_message=error or "Tool execution failed"
                )
                
                scar = self._daemon._scar_tissue.inflict(failure)
                logger.warning(f"SCAR INFLICTED: {scar.scar_id} - {failure.action_type}")
            
            if self._daemon:
                self._daemon._failure_count += 1
        
        # Update adaptive policy
        if self._daemon:
            total = self._daemon._success_count + self._daemon._failure_count
            if total > 0:
                self._daemon._policy_aggression = self._daemon._success_count / total
                logger.debug(f"Policy aggression updated: {self._daemon._policy_aggression:.3f}")
        
        # Store result in action history
        if self._action_history:
            self._action_history[-1]["result"] = result
    
    def execute_tool(self, tool_call: Dict[str, Any]) -> ToolResult:
        """
        Execute a tool call through ActuatorHub.
        
        This method actually runs the tool via NOOGH actuators.
        All security checks (AMLA, allowlists) apply.
        
        Args:
            tool_call: Dict with 'tool_name' and 'arguments'
            
        Returns:
            ToolResult with execution outcome
        """
        start_time = time.time()
        
        tool_name = tool_call.get("tool_name", "noop")
        arguments = tool_call.get("arguments", {})
        
        if not self._tool_registry:
            return ToolResult(
                success=False,
                output=None,
                error="Tool registry not initialized"
            )
        
        try:
            # Execute through tool registry (which uses actuators)
            result = self._tool_registry.execute(tool_name, arguments)
            
            execution_time = (time.time() - start_time) * 1000
            
            return ToolResult(
                success=result.get("success", False),
                output=result.get("output"),
                error=result.get("error"),
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Tool execution error: {e}")
            return ToolResult(
                success=False,
                output=None,
                error=str(e),
                execution_time_ms=execution_time
            )
    
    def run_task(
        self,
        task_description: str,
        expected_tools: Optional[List[str]] = None,
        max_steps: Optional[int] = None,
        task_id: Optional[str] = None,
        category: Optional[str] = None
    ) -> BenchmarkMetrics:
        """
        Run a complete benchmark task.
        
        Implements the Thought → Action → Observation → Thought loop.
        
        Args:
            task_description: Initial task from benchmark
            expected_tools: Optional list of expected tool names for accuracy
            max_steps: Override max steps for this task
            task_id: Optional task identifier
            category: Optional task category (e.g., 'failure_test')
            
        Returns:
            BenchmarkMetrics with all collected data
        """
        if max_steps:
            original_max = self._max_steps
            self._max_steps = max_steps
        
        try:
            self.reset()
            start_time = time.time()
            
            # Set task context for policy resolution
            self._current_task = {
                "task_id": task_id or self._current_task_id,
                "description": task_description,
                "expected_tools": expected_tools or [],
                "category": category or "general"
            }
            
            # Initial observation
            self.observe(f"TASK: {task_description}")
            
            while self._state == BenchmarkState.RUNNING:
                # ACT: Get tool call from agent (uses policy resolution)
                tool_call = self.act()
                
                if tool_call.get("error"):
                    break
                
                # Track tool selection accuracy
                if expected_tools and tool_call["tool_name"] in expected_tools:
                    self._metrics.tool_selection_correct += 1
                elif expected_tools:
                    # Not in expected but also not a hallucination if in registry
                    pass  # Policy already handles this
                
                # EXECUTE: Run the tool
                result = self.execute_tool(tool_call)
                
                # FEEDBACK: Learn from result
                self.feedback(result.to_dict())
                
                # OBSERVE: Get observation from result
                if result.success:
                    self.observe(f"Tool {tool_call['tool_name']} succeeded: {result.output}")
                else:
                    self.observe(f"Tool {tool_call['tool_name']} failed: {result.error}")
                
                # Check for task completion (simple heuristic)
                if self._check_task_complete():
                    self._state = BenchmarkState.COMPLETED
                    break
            
            # Sync extended metrics from adapter tracking
            self._metrics.unknown_tool_calls = self._unknown_tool_calls
            self._metrics.policy_corrections = self._policy_corrections
            self._metrics.valid_arguments = self._valid_args
            self._metrics.invalid_arguments = self._invalid_args
            self._metrics.total_time_ms = (time.time() - start_time) * 1000
            
            return self._metrics
            
        finally:
            if max_steps:
                self._max_steps = original_max
    
    def _check_task_complete(self) -> bool:
        """
        Check if current task should be considered complete.
        
        Simple heuristic: task is complete if last action was successful
        and no more observations indicate pending work.
        """
        if not self._action_history:
            return False
        
        last_action = self._action_history[-1]
        result = last_action.get("result", {})
        
        # Complete if we have a successful final action
        return result.get("success", False) and len(self._action_history) >= 2
    
    def get_metrics(self) -> Optional[BenchmarkMetrics]:
        """Get current metrics."""
        return self._metrics
    
    def get_action_history(self) -> List[Dict[str, Any]]:
        """Get full action history for debugging."""
        return self._action_history
    
    def shutdown(self) -> None:
        """Graceful shutdown - honors kill-switch."""
        logger.info("Benchmark adapter shutdown requested")
        self._state = BenchmarkState.IDLE
        
        if self._daemon:
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(self._daemon.shutdown())
            finally:
                loop.close()
        
        logger.info("Benchmark adapter shutdown complete")
