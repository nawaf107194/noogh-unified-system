"""
Test Concurrent State Isolation
Tests that concurrent requests don't interfere with each other.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from neural_engine.reasoning.react_loop import (
    ConstrainedReActLoop,
    CognitiveState,
)


class TestConcurrentStateIsolation:
    """Test that concurrent executions are properly isolated."""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_isolated(self):
        """
        CRITICAL: Verify concurrent requests maintain separate state.
        
        If two requests run simultaneously, their tool calls and observations
        should not mix.
        """
        # Create shared components
        call_log = []  # Track all calls with request ID
        
        async def mock_process(query, **kwargs):
            """Mock that returns different responses based on query."""
            await asyncio.sleep(0.01)  # Simulate processing
            
            if "request_a" in query.lower():
                return '{"thought": "Processing A", "answer": "Result A"}'
            else:
                return '{"thought": "Processing B", "answer": "Result B"}'
        
        mock_reasoning = AsyncMock()
        mock_reasoning.process = AsyncMock(side_effect=mock_process)
        
        mock_executor = MagicMock()
        
        # Create loop instance
        loop = ConstrainedReActLoop(
            reasoning_engine=mock_reasoning,
            tool_executor=mock_executor,
            max_iterations=1
        )
        
        # Run two requests concurrently
        task_a = asyncio.create_task(loop.run("request_a query"))
        task_b = asyncio.create_task(loop.run("request_b query"))
        
        result_a, result_b = await asyncio.gather(task_a, task_b)
        
        # Verify results are correct and not mixed
        assert "result a" in result_a.lower()
        assert "result b" in result_b.lower()
        
        # Should NOT have cross-contamination
        assert "result b" not in result_a.lower()
        assert "result a" not in result_b.lower()
    
    @pytest.mark.asyncio
    async def test_state_not_shared_between_instances(self):
        """
        Verify each loop instance has independent state.
        """
        mock_reasoning_1 = AsyncMock()
        mock_reasoning_1.process = AsyncMock(
            return_value='{"thought": "Instance 1", "answer": "Answer 1"}'
        )
        
        mock_reasoning_2 = AsyncMock()
        mock_reasoning_2.process = AsyncMock(
            return_value='{"thought": "Instance 2", "answer": "Answer 2"}'
        )
        
        mock_executor = MagicMock()
        
        # Create two separate instances
        loop_1 = ConstrainedReActLoop(
            reasoning_engine=mock_reasoning_1,
            tool_executor=mock_executor,
            max_iterations=1
        )
        
        loop_2 = ConstrainedReActLoop(
            reasoning_engine=mock_reasoning_2,
            tool_executor=mock_executor,
            max_iterations=1
        )
        
        # Run both
        result_1 = await loop_1.run("query 1")
        result_2 = await loop_2.run("query 2")
        
        # Each should get its own result
        assert "answer 1" in result_1.lower()
        assert "answer 2" in result_2.lower()
        
        # Verify reasoning engines were called independently
        assert mock_reasoning_1.process.call_count == 1
        assert mock_reasoning_2.process.call_count == 1
    
    @pytest.mark.asyncio
    async def test_observation_history_isolated(self):
        """
        CRITICAL: Verify observation history doesn't leak between requests.
        
        If request A sees observations from request B, that's a security issue.
        """
        observations_seen = {}
        
        async def mock_process_with_history(query, system_prompt=None, **kwargs):
            """Mock that logs what observations it sees in the prompt."""
            request_id = "A" if "request_a" in query.lower() else "B"
            
            # Parse prompt to see what observations are visible
            if system_prompt:
                observations_seen[request_id] = system_prompt
            
            await asyncio.sleep(0.01)
            
            # Return tool call first iteration, answer second
            if request_id not in observations_seen or len(observations_seen[request_id]) < 500:
                return f'{{"thought": "Need tool {request_id}", "tool": "tool_{request_id}", "args": {{}}}}'
            else:
                return f'{{"thought": "Done {request_id}", "answer": "Final {request_id}"}}'
        
        mock_reasoning = AsyncMock()
        mock_reasoning.process = AsyncMock(side_effect=mock_process_with_history)
        
        # Mock tool execution
        async def mock_execute(name, params):
            await asyncio.sleep(0.01)
            return {
                "success": True,
                "result": f"Observation from {name}"
            }
        
        mock_registry = MagicMock()
        mock_registry.execute = AsyncMock(side_effect=mock_execute)
        
        mock_executor = MagicMock()
        mock_executor.registry = mock_registry
        mock_executor.extract_tool_calls = MagicMock(
            side_effect=lambda resp: [
                (f"tool_{('A' if 'request_a' in resp else 'B')}", {})
            ] if "tool" in resp else []
        )
        
        loop = ConstrainedReActLoop(
            reasoning_engine=mock_reasoning,
            tool_executor=mock_executor,
            max_iterations=2
        )
        
        # Run concurrently
        task_a = asyncio.create_task(loop.run("request_a query"))
        task_b = asyncio.create_task(loop.run("request_b query"))
        
        await asyncio.gather(task_a, task_b)
        
        # Verify: Prompt for A should not contain observations from B
        if "A" in observations_seen and "B" in observations_seen:
            prompt_a = observations_seen["A"]
            prompt_b = observations_seen["B"]
            
            # A's prompt should not contain B's tool
            assert "tool_B" not in prompt_a or "tool_b" not in prompt_a.lower()
            
            # B's prompt should not contain A's tool
            assert "tool_A" not in prompt_b or "tool_a" not in prompt_b.lower()
    
    @pytest.mark.asyncio
    async def test_high_concurrency_stress(self):
        """
        Stress test: Run 10 concurrent requests, verify all complete correctly.
        """
        async def mock_process(query, **kwargs):
            # Extract request number from query
            import re
            match = re.search(r'request_(\d+)', query.lower())
            num = match.group(1) if match else "unknown"
            
            await asyncio.sleep(0.01)  # Simulate work
            return f'{{"thought": "Processing {num}", "answer": "Result {num}"}}'
        
        mock_reasoning = AsyncMock()
        mock_reasoning.process = AsyncMock(side_effect=mock_process)
        
        mock_executor = MagicMock()
        
        loop = ConstrainedReActLoop(
            reasoning_engine=mock_reasoning,
            tool_executor=mock_executor,
            max_iterations=1
        )
        
        # Run 10 concurrent requests
        num_requests = 10
        tasks = [
            asyncio.create_task(loop.run(f"request_{i} query"))
            for i in range(num_requests)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Verify all completed
        assert len(results) == num_requests
        
        # Verify each got correct result
        for i, result in enumerate(results):
            assert f"result {i}" in result.lower(), f"Request {i} got wrong result: {result}"
    
    @pytest.mark.asyncio
    async def test_error_in_one_request_doesnt_affect_others(self):
        """
        Verify that if one request fails, others continue normally.
        """
        call_count = {"value": 0}
        
        async def mock_process_with_error(query, **kwargs):
            call_count["value"] += 1
            
            # First call (request A) raises error
            if "request_a" in query.lower():
                raise Exception("Simulated error in request A")
            
            # Other calls succeed
            await asyncio.sleep(0.01)
            return '{"thought": "Success", "answer": "Success result"}'
        
        mock_reasoning = AsyncMock()
        mock_reasoning.process = AsyncMock(side_effect=mock_process_with_error)
        
        mock_executor = MagicMock()
        
        loop = ConstrainedReActLoop(
            reasoning_engine=mock_reasoning,
            tool_executor=mock_executor,
            max_iterations=1
        )
        
        # Run failing request alongside successful one
        task_a = asyncio.create_task(loop.run("request_a query"))
        task_b = asyncio.create_task(loop.run("request_b query"))
        
        # Gather with return_exceptions to capture both
        results = await asyncio.gather(task_a, task_b, return_exceptions=True)
        
        # Request A should have failed or returned error message
        result_a = results[0]
        # Request B should have succeeded
        result_b = results[1]
        
        # B should succeed despite A failing
        assert "success result" in result_b.lower()
    
    @pytest.mark.asyncio
    async def test_shared_tool_execution_safe(self):
        """
        Verify shared tool executor is thread-safe.
        
        Even if multiple requests use same tools concurrently,
        results should not be mixed.
        """
        execution_log = []
        
        async def mock_execute(name, params):
            # Log execution with timestamp
            import time
            execution_log.append({
                "time": time.time(),
                "tool": name,
                "params": params
            })
            
            await asyncio.sleep(0.01)  # Simulate work
            
            # Return result specific to params
            query_id = params.get("query_id", "unknown")
            return {
                "success": True,
                "result": f"Result for {query_id}"
            }
        
        mock_registry = MagicMock()
        mock_registry.execute = AsyncMock(side_effect=mock_execute)
        
        mock_executor = MagicMock()
        mock_executor.registry = mock_registry
        mock_executor.extract_tool_calls = MagicMock(
            side_effect=lambda resp: [
                ("shared_tool", {"query_id": resp.split(":")[1].strip()})
            ] if ":" in resp else []
        )
        
        async def mock_process(query, **kwargs):
            query_id = query.split("_")[1]
            return f"tool_call: {query_id}"
        
        mock_reasoning = AsyncMock()
        mock_reasoning.process = AsyncMock(side_effect=mock_process)
        
        loop = ConstrainedReActLoop(
            reasoning_engine=mock_reasoning,
            tool_executor=mock_executor,
            max_iterations=1
        )
        
        # Run 5 concurrent requests using same tool
        tasks = [
            asyncio.create_task(loop.run(f"request_{i}"))
            for i in range(5)
        ]
        
        await asyncio.gather(*tasks)
        
        # Verify all executions were logged independently
        assert len(execution_log) >= 5
        
        # Verify each request got its own params
        query_ids = [log["params"].get("query_id") for log in execution_log]
        # Should have multiple different IDs (0, 1, 2, 3, 4)
        unique_ids = set(query_ids)
        assert len(unique_ids) >= 3  # At least 3 different requests


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
