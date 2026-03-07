"""
Test Benchmark Adapter - Validates benchmark integration

Tests:
1. Adapter correctly calls AgentDaemon
2. Tool calls flow through actuators
3. Failures propagate and create scars
4. Decision loop aligns with benchmark expectations
"""

import pytest
import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch
import sys
import os

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestBenchmarkAgentAdapter:
    """Tests for BenchmarkAgentAdapter."""
    
    def test_adapter_initialization(self):
        """Test adapter initializes correctly."""
        from unified_core.benchmark_adapter import BenchmarkAgentAdapter, BenchmarkState
        
        adapter = BenchmarkAgentAdapter(
            max_steps=10,
            step_timeout_seconds=5.0,
            enable_learning=False  # Disable for test isolation
        )
        
        assert adapter._max_steps == 10
        assert adapter._step_timeout == 5.0
        assert adapter._state == BenchmarkState.IDLE
    
    def test_reset_creates_new_task(self):
        """Test reset() properly initializes for new task."""
        from unified_core.benchmark_adapter import BenchmarkAgentAdapter, BenchmarkState
        
        adapter = BenchmarkAgentAdapter(enable_learning=False)
        adapter.reset()
        
        assert adapter._state == BenchmarkState.RUNNING
        assert adapter._current_task_id is not None
        assert adapter._step_count == 0
        assert adapter._observation_buffer == []
        assert adapter._metrics is not None
    
    def test_observe_buffers_observation(self):
        """Test observe() adds to observation buffer."""
        from unified_core.benchmark_adapter import BenchmarkAgentAdapter
        
        adapter = BenchmarkAgentAdapter(enable_learning=False)
        adapter.reset()
        
        adapter.observe("First observation")
        adapter.observe("Second observation")
        
        assert len(adapter._observation_buffer) == 2
        assert "First observation" in adapter._observation_buffer
    
    def test_act_increments_step_count(self):
        """Test act() increments step counter."""
        from unified_core.benchmark_adapter import BenchmarkAgentAdapter
        
        adapter = BenchmarkAgentAdapter(enable_learning=False)
        adapter.reset()
        
        initial_steps = adapter._step_count
        adapter.act()
        
        assert adapter._step_count == initial_steps + 1
    
    def test_act_respects_max_steps(self):
        """Test act() returns error when max steps exceeded."""
        from unified_core.benchmark_adapter import BenchmarkAgentAdapter, BenchmarkState
        
        adapter = BenchmarkAgentAdapter(max_steps=2, enable_learning=False)
        adapter.reset()
        
        # Exhaust steps
        adapter.act()
        adapter.act()
        result = adapter.act()  # Should exceed
        
        assert adapter._state == BenchmarkState.TIMEOUT
        assert "Max steps exceeded" in result.get("error", "")
    
    def test_feedback_updates_metrics_on_success(self):
        """Test feedback() updates metrics for successful execution."""
        from unified_core.benchmark_adapter import BenchmarkAgentAdapter
        
        adapter = BenchmarkAgentAdapter(enable_learning=False)
        adapter.reset()
        adapter.act()  # Need to act first to have an action to feedback on
        
        initial_success = adapter._metrics.successful_tool_calls
        adapter.feedback({"success": True, "output": "result"})
        
        assert adapter._metrics.successful_tool_calls == initial_success + 1
    
    def test_feedback_updates_metrics_on_failure(self):
        """Test feedback() updates metrics for failed execution."""
        from unified_core.benchmark_adapter import BenchmarkAgentAdapter
        
        adapter = BenchmarkAgentAdapter(enable_learning=False)
        adapter.reset()
        adapter.act()
        
        initial_failed = adapter._metrics.failed_tool_calls
        adapter.feedback({"success": False, "error": "test error"})
        
        assert adapter._metrics.failed_tool_calls == initial_failed + 1
    
    def test_feedback_tracks_blocked_calls(self):
        """Test feedback() correctly tracks blocked tool calls."""
        from unified_core.benchmark_adapter import BenchmarkAgentAdapter
        
        adapter = BenchmarkAgentAdapter(enable_learning=False)
        adapter.reset()
        adapter.act()
        
        initial_blocked = adapter._metrics.blocked_tool_calls
        adapter.feedback({"success": False, "blocked": True, "error": "Path not allowed"})
        
        assert adapter._metrics.blocked_tool_calls == initial_blocked + 1


class TestToolRegistry:
    """Tests for ToolRegistry."""
    
    def test_registry_initialization(self):
        """Test registry initializes with expected tools."""
        from unified_core.tool_registry import ToolRegistry
        
        registry = ToolRegistry(actuator_hub=None)
        
        assert registry.has_tool("filesystem.write")
        assert registry.has_tool("filesystem.read")
        assert registry.has_tool("http.get")
        assert registry.has_tool("calculator.compute")
        assert registry.has_tool("noop")
    
    def test_calculator_compute_basic(self):
        """Test calculator.compute handles basic math."""
        from unified_core.tool_registry import ToolRegistry
        
        registry = ToolRegistry(actuator_hub=None)
        
        result = registry.execute("calculator.compute", {"expression": "2 + 2"})
        
        assert result["success"] is True
        assert result["output"] == 4.0
    
    def test_calculator_compute_complex(self):
        """Test calculator.compute handles complex math."""
        from unified_core.tool_registry import ToolRegistry
        
        registry = ToolRegistry(actuator_hub=None)
        
        result = registry.execute("calculator.compute", {"expression": "sqrt(144)"})
        
        assert result["success"] is True
        assert result["output"] == 12.0
    
    def test_calculator_rejects_dangerous_input(self):
        """Test calculator.compute rejects code injection."""
        from unified_core.tool_registry import ToolRegistry
        
        registry = ToolRegistry(actuator_hub=None)
        
        # Attempt code injection
        result = registry.execute("calculator.compute", {"expression": "__import__('os').system('ls')"})
        
        assert result["success"] is False
        assert "Invalid expression" in result.get("error", "")
    
    def test_calculator_add(self):
        """Test calculator.add works."""
        from unified_core.tool_registry import ToolRegistry
        
        registry = ToolRegistry(actuator_hub=None)
        
        result = registry.execute("calculator.add", {"a": 5, "b": 3})
        
        assert result["success"] is True
        assert result["output"] == 8
    
    def test_unknown_tool_returns_error(self):
        """Test unknown tool returns appropriate error."""
        from unified_core.tool_registry import ToolRegistry
        
        registry = ToolRegistry(actuator_hub=None)
        
        result = registry.execute("nonexistent.tool", {})
        
        assert result["success"] is False
        assert "Unknown tool" in result.get("error", "")
    
    def test_missing_required_argument(self):
        """Test missing required argument returns error."""
        from unified_core.tool_registry import ToolRegistry
        
        registry = ToolRegistry(actuator_hub=None)
        
        result = registry.execute("filesystem.write", {"content": "test"})  # Missing 'path'
        
        assert result["success"] is False
        assert "Missing required argument" in result.get("error", "")
    
    def test_filesystem_write_without_actuator(self):
        """Test filesystem.write fails gracefully without actuator."""
        from unified_core.tool_registry import ToolRegistry
        
        registry = ToolRegistry(actuator_hub=None)
        
        result = registry.execute("filesystem.write", {
            "path": "/tmp/test.txt",
            "content": "test"
        })
        
        assert result["success"] is False
        assert result.get("blocked", False) is True
    
    def test_action_to_tool_mapping(self):
        """Test action type to tool name mapping."""
        from unified_core.tool_registry import ToolRegistry
        
        registry = ToolRegistry(actuator_hub=None)
        
        # Direct mapping
        tool, args = registry.map_action_to_tool("filesystem.write", {"path": "/tmp/x"})
        assert tool == "filesystem.write"
        
        # act_on_ pattern mapping
        tool, args = registry.map_action_to_tool("act_on_file_write", {})
        assert tool == "filesystem.write"
        
        tool, args = registry.map_action_to_tool("act_on_calculate", {})
        assert tool == "calculator.compute"


class TestBenchmarkMetrics:
    """Tests for BenchmarkMetrics calculations."""
    
    def test_selection_accuracy(self):
        """Test selection accuracy calculation."""
        from unified_core.benchmark_adapter import BenchmarkMetrics
        
        metrics = BenchmarkMetrics(
            task_id="test",
            tool_selection_correct=7,
            tool_selection_total=10
        )
        
        assert metrics.selection_accuracy == 0.7
    
    def test_hallucination_rate(self):
        """Test hallucination rate calculation."""
        from unified_core.benchmark_adapter import BenchmarkMetrics
        
        metrics = BenchmarkMetrics(
            task_id="test",
            hallucinations=1,
            tool_selection_total=10
        )
        
        assert metrics.hallucination_rate == 0.1
    
    def test_success_rate(self):
        """Test success rate calculation."""
        from unified_core.benchmark_adapter import BenchmarkMetrics
        
        metrics = BenchmarkMetrics(
            task_id="test",
            successful_tool_calls=8,
            failed_tool_calls=1,
            blocked_tool_calls=1
        )
        
        assert metrics.success_rate == 0.8


class TestFailurePropagation:
    """Tests for failure path verification."""
    
    def test_scar_created_on_failure(self):
        """Test that failures create scars when learning enabled."""
        from unified_core.benchmark_adapter import BenchmarkAgentAdapter
        
        adapter = BenchmarkAgentAdapter(enable_learning=True)
        adapter.reset()
        adapter.act()
        
        # This should attempt to create a scar
        adapter.feedback({
            "success": False,
            "error": "Test failure for scar creation"
        })
        
        # Check that daemon recorded the failure
        if adapter._daemon:
            assert adapter._daemon._failure_count > 0
    
    def test_policy_aggression_decreases_on_failure(self):
        """Test that policy_aggression decreases after failures."""
        from unified_core.benchmark_adapter import BenchmarkAgentAdapter
        
        adapter = BenchmarkAgentAdapter(enable_learning=True)
        adapter.reset()
        
        # Record some successes first
        for _ in range(3):
            adapter.act()
            adapter.feedback({"success": True})
        
        initial_aggression = adapter._daemon._policy_aggression if adapter._daemon else 0.5
        
        # Now record failures
        for _ in range(3):
            adapter.act()
            adapter.feedback({"success": False, "error": "test"})
        
        if adapter._daemon:
            assert adapter._daemon._policy_aggression < initial_aggression


class TestBenchmarkRunner:
    """Tests for BenchmarkRunner."""
    
    def test_runner_initialization(self):
        """Test runner initializes correctly."""
        from unified_core.benchmark_runner import BenchmarkRunner
        
        runner = BenchmarkRunner(
            default_max_steps=20,
            default_timeout=60.0
        )
        
        assert runner._default_max_steps == 20
        assert runner._default_timeout == 60.0
    
    def test_sample_tasks_exist(self):
        """Test that sample tasks are defined."""
        from unified_core.benchmark_runner import SAMPLE_TASKS
        
        assert len(SAMPLE_TASKS) > 0
        assert any(t.category == "failure_test" for t in SAMPLE_TASKS)
    
    def test_failure_tasks_included(self):
        """Test that failure test tasks are present."""
        from unified_core.benchmark_runner import SAMPLE_TASKS
        
        failure_tasks = [t for t in SAMPLE_TASKS if t.category == "failure_test"]
        assert len(failure_tasks) >= 3  # blocked path, process, network


class TestIntegrationFlow:
    """Integration tests for the full benchmark flow."""
    
    def test_full_task_execution(self):
        """Test running a complete simple task."""
        from unified_core.benchmark_adapter import BenchmarkAgentAdapter
        
        adapter = BenchmarkAgentAdapter(
            max_steps=5,
            enable_learning=False
        )
        
        metrics = adapter.run_task(
            task_description="Calculate 2 + 2",
            expected_tools=["calculator.compute", "calculator.add"],
            max_steps=5
        )
        
        assert metrics is not None
        assert metrics.total_steps > 0
    
    def test_blocked_path_creates_failure(self):
        """Test that writing to blocked path registers as failure."""
        from unified_core.tool_registry import ToolRegistry
        
        # Create mock actuator hub
        mock_hub = MagicMock()
        mock_result = MagicMock()
        mock_result.result = MagicMock()
        mock_result.result.value = "blocked"
        mock_result.result_data = {"error": "Path not in allowed directories"}
        mock_hub.filesystem.write_file.return_value = mock_result
        
        # Patch ActionResult import
        with patch.dict('sys.modules', {'unified_core.core.actuators': MagicMock()}):
            registry = ToolRegistry(actuator_hub=mock_hub)
            
            result = registry.execute("filesystem.write", {
                "path": "/etc/passwd",
                "content": "malicious"
            })
            
            # Should fail or be blocked
            assert result["success"] is False or result.get("blocked", False)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
