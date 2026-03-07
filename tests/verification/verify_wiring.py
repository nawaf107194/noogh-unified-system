import asyncio
import os
import sys
from unittest.mock import MagicMock, AsyncMock

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'gateway'))
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

# Mock missing dependencies for verification environment
from unittest.mock import MagicMock
sys.modules["chromadb"] = MagicMock()
sys.modules["chromadb.config"] = MagicMock()
sys.modules["sentence_transformers"] = MagicMock()
sys.modules["datasets"] = MagicMock()

from gateway.app.core.agent_kernel import AgentKernel
from gateway.app.core.auth import AuthContext
from gateway.app.integrations.neural_client import NeuralClient, NeuralResponse

async def test_wiring():
    print("🧪 Testing Gateway -> Neural Engine Wiring...")
    
    # 1. Setup Mock Neural Client
    mock_client = AsyncMock(spec=NeuralClient)
    # Mock the _request method to return a success response
    mock_client._request.return_value = NeuralResponse(
        success=True,
        data={
            "conclusion": "Apple stock analysis requires financial expertise. [Neural Engine Response]",
            "confidence": 0.95,
            "reasoning_trace": ["Identified financial domain", "Consulted market data"],
            "suggested_actions": ["Buy", "Hold"]
        }
    )
    
    # 2. Instantiate Kernel with Mock Client injection
    # Since we can't easily inject into __init__ without modifying it further,
    # we'll monkey-patch the client after init.
    kernel = AgentKernel(enable_router=True)
    kernel.neural_client = mock_client
    
    # 3. Create a task that triggers delegation
    # "stock" triggers the finance rule in IntelligentRouter
    task = "Analyze the recent performance of AAPL stock."
    auth = AuthContext(token="mock_token", scopes={"*"})
    
    print(f"📝 Task: {task}")
    
    # 4. Run Process in a separate thread to simulate production environment
    # where AgentKernel runs in a worker thread and can use asyncio.run()
    # independently of the main loop if needed, or ensuring no conflict.
    
    # Actually, simpler: Test _delegate_if_needed directly since we know process() calls it.
    # But we want to verify the integration.
    
    # If we run kernel.process directly here, it sees the loop from main().
    # Let's run it in an executor.
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(kernel.process, task, auth)
        result = future.result()
    
    # 5. Verify Delegation
    print(f"🔍 Result Success: {result.success}")
    print(f"🔍 Result Answer: {result.answer}")
    print(f"🔍 Metadata: {result.metadata}")
    
    if result.metadata and result.metadata.get("delegated"):
        print("✅ SUCCESS: Task was correctly delegated!")
        print(f"   Target: {result.metadata.get('delegate_to')}")
        print(f"   Neural Trace: {result.metadata.get('neural_trace')}")
    else:
        print("❌ FAILURE: Task was NOT delegated.")
        print(f"   Router Decision: {kernel.router.analyze_task(task)}")
        sys.exit(1)

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(test_wiring())
