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
sys.modules["sentence_transformers"] = MagicMock()
sys.modules["datasets"] = MagicMock()

import logging
logging.basicConfig(level=logging.INFO)

from gateway.app.core.agent_kernel import AgentKernel
from gateway.app.integrations.neural_client import NeuralClient, NeuralResponse
from gateway.app.core.auth import AuthContext

async def test_unified_integration():
    print("🧪 Testing Final Unified Integration...")
    
    # 1. Setup Mock Neural Client
    mock_client = AsyncMock(spec=NeuralClient)
    
    # Mock search response
    mock_client.recall_memory.return_value = NeuralResponse(
        success=True,
        data={"memories": [{"content": "Past insight: avoid division by zero", "success": True}]}
    )
    
    # Mock store response
    mock_client.store_memory.return_value = NeuralResponse(success=True, data={})
    
    # 2. Instantiate Kernel
    print("Initializing Kernel...")
    kernel = AgentKernel(
        enable_learning=False, 
        enable_router=False, 
        enable_dream_mode=False
    )
    
    # Inject mock client
    kernel.neural_client = mock_client
    # Re-init memory with client
    from gateway.app.core.memory import SemanticMemory
    kernel.semantic_memory = SemanticMemory(neural_client=mock_client)
    
    # 3. Test Task Execution with Memory Recall
    print("Test: Task with memory recall...")
    auth = AuthContext(token="test", scopes={"*"})
    
    # Mock brain to avoid LLM call
    mock_brain = MagicMock()
    mock_brain.generate.return_value = "Action: calculator\nPlan: divide 10 by 2"
    kernel.remote_brain = mock_brain
    
    # Simulate first turn in a thread (like FastAPI sync route)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, kernel.process, "Calculate 10/2", auth)
    
    print(f"Result success: {result.success}")
    # Verify search was called
    mock_client.recall_memory.assert_called()
    print("✅ Verified: Semantic memory search triggered during task.")
    
    # 4. Verify Task Storage (Persistence Sync)
    print("Test: Persistence Sync...")
    # Give background task a moment to run
    await asyncio.sleep(0.5)
    
    mock_client.store_memory.assert_called()
    print("✅ Verified: Task result stored in Unified Semantic Memory.")
    
    print("\n🚀 ALL INTEGRATION TESTS PASSED (MOCKED)!")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(test_unified_integration())
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
