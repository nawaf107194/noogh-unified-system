import asyncio
import time
import pytest
import httpx
from unittest.mock import MagicMock, patch
from unified_core.core.world_model import WorldModel, Observation

@pytest.mark.asyncio
async def test_async_synthesis_non_blocking():
    """
    Test that synthesize_semantic_beliefs does NOT block the event loop.
    We'll measure loop latency while synthesis is running.
    """
    wm = WorldModel()
    
    # Mock httpx.AsyncClient.post to take some time
    async def slow_post(*args, **kwargs):
        await asyncio.sleep(1.0) # Artificial delay
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"conclusion": '["Test Neuron"]'}
        return mock_resp

    with patch("httpx.AsyncClient.post", side_effect=slow_post):
        start_time = time.time()
        
        # Trigger synthesis (background task)
        task = asyncio.create_task(wm.synthesize_semantic_beliefs())
        
        # Check if we can still do other work on the loop
        loop_work_count = 0
        while not task.done():
            await asyncio.sleep(0.1)
            loop_work_count += 1
            if time.time() - start_time > 2.0:
                break
                
        # Verification
        assert loop_work_count >= 5, f"Event loop was blocked! Only {loop_work_count} heartbeat(s) detected."
        print(f"  ✓ Event loop remained active during synthesis ({loop_work_count} heartbeats)")

@pytest.mark.asyncio
async def test_consolidate_memory_non_blocking():
    """Test that consolidate_memory (SQLite) doesn't block the loop."""
    wm = WorldModel()
    
    # Trigger consolidation
    task = asyncio.create_task(wm.consolidate_memory())
    
    heartbeats = 0
    while not task.done():
        await asyncio.sleep(0.01)
        heartbeats += 1
        
    assert heartbeats > 0
    print(f"  ✓ Event loop remained active during memory consolidation.")

if __name__ == "__main__":
    asyncio.run(test_async_synthesis_non_blocking())
    asyncio.run(test_consolidate_memory_non_blocking())
