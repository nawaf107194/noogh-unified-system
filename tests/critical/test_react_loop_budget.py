"""
Test ReAct Loop Budget Enforcement
Tests that MAX_ITERATIONS and TOOL_BUDGET are properly enforced.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# Import the constrained ReAct loop
from neural_engine.reasoning.react_loop import (
    ConstrainedReActLoop,
    CognitiveState,
    ReActAction,
    ActionType,
)


class TestReActBudgetEnforcement:
    """Test ReAct loop budget constraints."""
    
    @pytest.mark.asyncio
    async def test_max_iterations_enforced(self):
        """
        CRITICAL: Verify MAX_ITERATIONS is enforced.
        
        Even if LLM keeps returning tool calls, loop should stop after MAX_ITERATIONS.
        """
        # Create mock reasoning engine that always returns tool call
        mock_reasoning = AsyncMock()
        mock_reasoning.process = AsyncMock(return_value=json.dumps({
            "thought": "Keep going",
            "tool": "test_tool",
            "args": {}
        }))
        
        # Create mock tool registry
        mock_registry = MagicMock()
        mock_registry.execute = AsyncMock(return_value={
            "success": True,
            "result": "test result"
        })
        
        # Create mock executor
        mock_executor = MagicMock()
        mock_executor.registry = mock_registry
        
        # Create loop with mocked components
        loop = ConstrainedReActLoop(
            reasoning_engine=mock_reasoning,
            tool_executor=mock_executor,
            max_iterations=2  # Should stop after 2 iterations
        )
        
        # Run
        result = await loop.run("test query")
        
        # Verify: Should have called LLM exactly MAX_ITERATIONS times
        # Even though LLM kept returning tool calls
        assert mock_reasoning.process.call_count == 2
        
        # Result should contain termination message
        assert "iterations" in result.lower() or "limit" in result.lower()
    
    @pytest.mark.asyncio
    async def test_final_answer_stops_early(self):
        """
        Verify that FINAL_ANSWER stops loop before MAX_ITERATIONS.
        """
        # Mock that returns FINAL_ANSWER on first call
        mock_reasoning = AsyncMock()
        mock_reasoning.process = AsyncMock(return_value=json.dumps({
            "thought": "I can answer directly",
            "answer": "This is the final answer"
        }))
        
        mock_executor = MagicMock()
        
        loop = ConstrainedReActLoop(
            reasoning_engine=mock_reasoning,
            tool_executor=mock_executor,
            max_iterations=10  # Max is 10, but should stop at 1
        )
        
        result = await loop.run("test query")
        
        # Should have called LLM only once
        assert mock_reasoning.process.call_count == 1
        
        # Result should be the final answer
        assert "final answer" in result.lower()
    
    @pytest.mark.asyncio
    async def test_tool_budget_per_iteration(self):
        """
        CRITICAL: Verify TOOL_BUDGET_PER_CYCLE is enforced.
        
        If LLM returns multiple tool calls in one response, only first N should execute.
        """
        # Mock that returns 5 tool calls in JSON
        mock_reasoning = AsyncMock()
        mock_reasoning.process = AsyncMock(return_value=json.dumps({
            "thought": "Need many tools",
            "tools": [
                {"tool": "tool1", "args": {}},
                {"tool": "tool2", "args": {}},
                {"tool": "tool3", "args": {}},
                {"tool": "tool4", "args": {}},
                {"tool": "tool5", "args": {}},
            ]
        }))
        
        # Track tool executions
        tool_calls = []
        
        async def mock_execute(name, params):
            tool_calls.append(name)
            return {"success": True, "result": "ok"}
        
        mock_registry = MagicMock()
        mock_registry.execute = AsyncMock(side_effect=mock_execute)
        
        mock_executor = MagicMock()
        mock_executor.registry = mock_registry
        mock_executor.max_tool_calls = 1  # BUDGET: Only 1 tool per cycle
        
        # Mock extract to return all 5 tools
        mock_executor.extract_tool_calls = MagicMock(return_value=[
            ("tool1", {}),
            ("tool2", {}),
            ("tool3", {}),
            ("tool4", {}),
            ("tool5", {}),
        ])
        
        loop = ConstrainedReActLoop(
            reasoning_engine=mock_reasoning,
            tool_executor=mock_executor,
            max_iterations=1
        )
        
        result = await loop.run("test query")
        
        # Should have executed only 1 tool (budget limit)
        # Note: This test verifies executor budget, not loop budget
        assert len(tool_calls) <= 1
    
    @pytest.mark.asyncio
    async def test_observation_truncation(self):
        """
        Verify observations are truncated to OBSERVATION_MAX_CHARS.
        """
        # Mock that returns huge observation
        huge_result = "x" * 10000  # 10KB result
        
        mock_reasoning = AsyncMock()
        mock_reasoning.process = AsyncMock(return_value=json.dumps({
            "thought": "Need data",
            "tool": "get_data",
            "args": {}
        }))
        
        mock_registry = MagicMock()
        mock_registry.execute = AsyncMock(return_value={
            "success": True,
            "result": huge_result
        })
        
        mock_executor = MagicMock()
        mock_executor.registry = mock_registry
        mock_executor.extract_tool_calls = MagicMock(return_value=[("get_data", {})])
        
        loop = ConstrainedReActLoop(
            reasoning_engine=mock_reasoning,
            tool_executor=mock_executor,
            max_iterations=1,
            observation_max_chars=500  # Truncate to 500 chars
        )
        
        # Patch _build_reasoning_prompt to capture state
        original_build = loop._build_reasoning_prompt
        captured_prompts = []
        
        def capture_prompt(state):
            prompt = original_build(state)
            captured_prompts.append(prompt)
            return prompt
        
        loop._build_reasoning_prompt = capture_prompt
        
        result = await loop.run("test query")
        
        # Check that observations in prompt are truncated
        # (Should not contain full 10KB result)
        if captured_prompts:
            last_prompt = captured_prompts[-1]
            assert len(last_prompt) < 10000  # Much smaller than full result
    
    @pytest.mark.asyncio
    async def test_timeout_enforcement(self):
        """
        Verify LLM timeout is enforced (from previous fix).
        """
        import asyncio
        
        # Mock that hangs forever
        async def hanging_process(*args, **kwargs):
            await asyncio.sleep(100)  # Hang for 100 seconds
            return "should not reach here"
        
        mock_reasoning = AsyncMock()
        mock_reasoning.process = AsyncMock(side_effect=hanging_process)
        
        mock_executor = MagicMock()
        
        loop = ConstrainedReActLoop(
            reasoning_engine=mock_reasoning,
            tool_executor=mock_executor,
            max_iterations=1
        )
        
        # Should timeout and return error message, not hang forever
        start_time = asyncio.get_event_loop().time()
        result = await loop.run("test query")
        end_time = asyncio.get_event_loop().time()
        
        # Should complete in ~30 seconds (timeout), not 100
        duration = end_time - start_time
        assert duration < 35  # 30s timeout + 5s margin
        
        # Result should indicate timeout
        assert "timeout" in result.lower() or "انتهت مهلة" in result
    
    @pytest.mark.asyncio
    async def test_zero_iterations_blocks_execution(self):
        """
        Edge case: MAX_ITERATIONS=0 should prevent any execution.
        """
        mock_reasoning = AsyncMock()
        mock_executor = MagicMock()
        
        loop = ConstrainedReActLoop(
            reasoning_engine=mock_reasoning,
            tool_executor=mock_executor,
            max_iterations=0  # No iterations allowed
        )
        
        result = await loop.run("test query")
        
        # Should not have called LLM at all
        assert mock_reasoning.process.call_count == 0
        
        # Should return error message
        assert result is not None


import json

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
