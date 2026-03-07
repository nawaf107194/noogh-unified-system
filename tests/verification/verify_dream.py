import asyncio
import os
import sys
import unittest.mock
from unittest.mock import MagicMock, AsyncMock

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'gateway'))
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

# Mock missing dependencies
sys.modules["chromadb"] = MagicMock()
sys.modules["chromadb.config"] = MagicMock()
sys.modules["sentence_transformers"] = MagicMock()
sys.modules["datasets"] = MagicMock()

# Mock GPUMemoryManager before importing AgentKernel
sys.modules["gateway.app.core.gpu_manager"] = MagicMock()

import logging
logging.basicConfig(level=logging.INFO)

from gateway.app.core.agent_kernel import AgentKernel
from gateway.app.integrations.neural_client import NeuralClient, NeuralResponse

async def test_dream_wiring():
    print("🧪 Testing Dream System Wiring...")
    
    # Setup Mock Neural Client
    mock_client = AsyncMock(spec=NeuralClient)
    mock_client.trigger_dream.return_value = NeuralResponse(
        success=True,
        data={
            "status": "dream_complete",
            "stats": {"insights": 3}
        }
    )
    
    # Instantiate Kernel 
    print("Initializing Kernel...")
    # enable_learning=False to avoid distillation service init
    kernel = AgentKernel(enable_dream_mode=True, enable_learning=False, enable_router=False)
    
    # Inject mock client
    kernel.neural_client = mock_client
    
    worker = kernel.dream_worker
    if not worker:
        print("❌ FAILURE: DreamWorker not initialized")
        sys.exit(1)
        
    print("DreamWorker attached. Starting test cycle...")
    
    # Stop any auto-run
    worker.stop()
    await asyncio.sleep(0.1)
    
    # Patch asyncio in dream_worker namespace ONLY
    # We want to mock sleep() but keep other functions like create_task working?
    # DreamWorker uses asyncio.sleep and asyncio.CancelledError
    
    real_asyncio = sys.modules['asyncio']
    
    # Create a proxy object that delegates to real_asyncio but overrides sleep
    class AsyncioProxy:
        def __getattr__(self, name):
            return getattr(real_asyncio, name)
            
    proxy = AsyncioProxy()
    # Mock sleep specifically
    # Use real sleep for short duration to avoid spin loop
    async def fast_sleep(seconds):
        await real_asyncio.sleep(0.05)
    
    proxy.sleep = AsyncMock(side_effect=fast_sleep)
    
    # Patch the IMPORT in the module
    with unittest.mock.patch('gateway.app.core.dream_worker.asyncio', proxy):
        # Start worker
        print(f"Worker state before start: {worker.is_running}")
        worker.is_running = False # Force reset
        
        print("Starting worker with mocked sleep...")
        task = asyncio.create_task(worker.start())
        
        # Verify mocked sleep was called?
        # worker start -> log -> sleep(10)
        # We need to yield to let worker run.
        # await asyncio.sleep(0.2) in TEST uses REAL asyncio (global).
        
        print("Waiting for worker loop...")
        await asyncio.sleep(0.5) 
        
        # Verify trigger_dream was called
        try:
             # Check if proxy.sleep was called
             print(f"Proxy sleep called count: {proxy.sleep.call_count}")
             proxy.sleep.assert_called()
             print("✅ AsyncioProxy.sleep called.")
             
             mock_client.trigger_dream.assert_called()
             print("✅ SUCCESS: DreamWorker triggered Neural Engine dream mode!")
             print(f"   Call args: {mock_client.trigger_dream.call_args}")
        except AssertionError as e:
            print(f"❌ FAILURE: Verification failed: {e}")
            if not proxy.sleep.called:
                print("   Mock sleep was not even called.")
            if not mock_client.trigger_dream.called:
                print("   Trigger dream was not called.")
            
            # Debug log check
            # We can't easily check logs here without capturing handler
            
        # Cleanup
        worker.stop()
        # Mock sleep again to let it exit loop instantly
        proxy.sleep.return_value = None
        try:
             await asyncio.wait_for(task, timeout=1.0)
        except Exception:
             pass

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(test_dream_wiring())
