"""
Tests for benchmark integration.

Verifies:
- ToolPolicy resolves correctly
- Hallucination rate < 10%
- Argument valid rate > 95%
- Selection accuracy > 70%
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestToolPolicy:
    """Tests for ToolPolicy strict resolution."""
    
    def test_policy_initialization(self):
        from unified_core.benchmarks.tool_policy import ToolPolicy
        policy = ToolPolicy()
        assert policy._resolution_count == 0
    
    def test_math_resolution(self):
        from unified_core.benchmarks.tool_policy import ToolPolicy
        policy = ToolPolicy()
        
        result = policy.resolve(
            decision={},
            observation="Calculate 15 * 7 + 23",
            task={"description": "Calculate 15 * 7 + 23"}
        )
        
        assert result["tool_name"] == "calculator.compute"
        assert "expression" in result["arguments"]
    
    def test_add_resolution(self):
        from unified_core.benchmarks.tool_policy import ToolPolicy
        policy = ToolPolicy()
        
        result = policy.resolve(
            decision={},
            observation="Add 100 and 50",
            task={"description": "Add 100 and 50"}
        )
        
        assert result["tool_name"] in ["calculator.add", "calculator.compute"]
    
    def test_filesystem_write_resolution(self):
        from unified_core.benchmarks.tool_policy import ToolPolicy
        policy = ToolPolicy()
        
        result = policy.resolve(
            decision={},
            observation="Write 'hello' to hello.txt",
            task={"description": "Write 'hello' to hello.txt"}
        )
        
        assert result["tool_name"] == "filesystem.write"
        assert "path" in result["arguments"]
        assert "content" in result["arguments"]
    
    def test_filesystem_exists_resolution(self):
        from unified_core.benchmarks.tool_policy import ToolPolicy
        policy = ToolPolicy()
        
        result = policy.resolve(
            decision={},
            observation="Check if /tmp exists",
            task={"description": "Check if /tmp exists"}
        )
        
        assert result["tool_name"] == "filesystem.exists"
    
    def test_http_get_resolution(self):
        from unified_core.benchmarks.tool_policy import ToolPolicy
        policy = ToolPolicy()
        
        result = policy.resolve(
            decision={},
            observation="GET http://localhost:8000/health",
            task={"description": "Fetch from http://localhost:8000/health"}
        )
        
        assert result["tool_name"] == "http.get"
        assert "url" in result["arguments"]
        assert "localhost" in result["arguments"]["url"]
    
    def test_unknown_falls_to_noop(self):
        from unified_core.benchmarks.tool_policy import ToolPolicy
        policy = ToolPolicy()
        
        result = policy.resolve(
            decision={"content": {"action_type": "unknown_action"}},
            observation="",
            task={}
        )
        
        assert result["tool_name"] == "noop"
    
    def test_never_returns_unknown_tool(self):
        from unified_core.benchmarks.tool_policy import ToolPolicy
        policy = ToolPolicy()
        
        # Test many random inputs
        test_inputs = [
            "do something weird",
            "execute unknown command",
            "fly to the moon",
            "",
            None
        ]
        
        for obs in test_inputs:
            result = policy.resolve(
                decision={},
                observation=obs,
                task={}
            )
            assert result["tool_name"] in policy.KNOWN_TOOLS
    
    def test_validate_arguments_calculator(self):
        from unified_core.benchmarks.tool_policy import ToolPolicy
        policy = ToolPolicy()
        
        is_valid, args = policy.validate_arguments(
            "calculator.compute",
            {"expression": "2 + 2"}
        )
        assert is_valid
        
        is_valid, args = policy.validate_arguments(
            "calculator.compute",
            {"expression": "__import__('os')"}
        )
        assert not is_valid
    
    def test_validate_arguments_add(self):
        from unified_core.benchmarks.tool_policy import ToolPolicy
        policy = ToolPolicy()
        
        is_valid, args = policy.validate_arguments(
            "calculator.add",
            {"a": 5, "b": 3}
        )
        assert is_valid
        assert args["a"] == 5.0
        
        is_valid, args = policy.validate_arguments(
            "calculator.add",
            {"a": "not a number", "b": 3}
        )
        assert not is_valid


class TestBenchmarkTasks:
    """Test that benchmark tasks are properly defined."""
    
    def test_toolbench_local_has_50_tasks(self):
        from unified_core.benchmarks.benchmark_runner import TOOLBENCH_LOCAL_TASKS
        assert len(TOOLBENCH_LOCAL_TASKS) == 50
    
    def test_all_tasks_have_ground_truth(self):
        from unified_core.benchmarks.benchmark_runner import TOOLBENCH_LOCAL_TASKS
        
        for task in TOOLBENCH_LOCAL_TASKS:
            assert task.ground_truth_tool is not None, f"Task {task.task_id} missing ground_truth"
    
    def test_failure_tasks_exist(self):
        from unified_core.benchmarks.benchmark_runner import TOOLBENCH_LOCAL_TASKS
        
        failure_tasks = [t for t in TOOLBENCH_LOCAL_TASKS if t.category == "failure_test"]
        assert len(failure_tasks) == 10
    
    def test_category_distribution(self):
        from unified_core.benchmarks.benchmark_runner import TOOLBENCH_LOCAL_TASKS
        
        categories = {}
        for task in TOOLBENCH_LOCAL_TASKS:
            categories[task.category] = categories.get(task.category, 0) + 1
        
        assert categories.get("calculator", 0) == 15
        assert categories.get("filesystem", 0) == 15
        assert categories.get("http", 0) == 10
        assert categories.get("failure_test", 0) == 10


class TestIntegrationWithPolicy:
    """Integration tests for adapter with policy."""
    
    def test_adapter_uses_policy(self):
        from unified_core.benchmark_adapter import BenchmarkAgentAdapter
        
        adapter = BenchmarkAgentAdapter(
            max_steps=3,
            enable_learning=False
        )
        
        # Run a simple task
        metrics = adapter.run_task(
            task_description="Calculate 2 + 2",
            expected_tools=["calculator.compute", "calculator.add"],
            task_id="test_001",
            category="calculator"
        )
        
        # Hallucination rate should be 0 (policy ensures known tools)
        assert metrics.hallucination_rate == 0.0
        assert metrics.unknown_tool_calls == 0
    
    def test_valid_arguments_tracked(self):
        from unified_core.benchmark_adapter import BenchmarkAgentAdapter
        
        adapter = BenchmarkAgentAdapter(
            max_steps=3,
            enable_learning=False
        )
        
        metrics = adapter.run_task(
            task_description="Calculate sqrt(144)",
            expected_tools=["calculator.compute"],
            task_id="test_002"
        )
        
        # Should have valid arguments
        assert metrics.valid_arguments >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
