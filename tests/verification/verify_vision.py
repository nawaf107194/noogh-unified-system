import asyncio
import os
import sys
from unittest.mock import MagicMock, AsyncMock

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'gateway'))
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

# Mock missing dependencies
sys.modules["chromadb"] = MagicMock()
sys.modules["chromadb.config"] = MagicMock()
sys.modules["sentence_transformers"] = MagicMock()
sys.modules["datasets"] = MagicMock()

from gateway.app.core.agent_kernel import AgentKernel
from gateway.app.core.auth import AuthContext
from gateway.app.integrations.neural_client import NeuralClient, NeuralResponse

async def test_vision_wiring():
    print("🧪 Testing Vision System Wiring...")
    
    # Setup Mock Neural Client
    mock_client = AsyncMock(spec=NeuralClient)
    mock_client.process_vision.return_value = NeuralResponse(
        success=True,
        data={
            "results": "A black cat sitting on a fence."
        }
    )
    
    # Instantiate Kernel and inject mock
    kernel = AgentKernel(enable_router=True)
    kernel.neural_client = mock_client
    
    # Task with image
    image_path = "./data/cat.jpg"
    task = f"What is in this image {image_path}?"
    auth = AuthContext(token="mock_token", scopes={"*"})
    
    print(f"📝 Task: {task}")
    
    # Run in ThreadPoolExecutor to verify sync->async delegation wrapper
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(kernel.process, task, auth)
        result = future.result()
        
    # Verify
    print(f"🔍 Result Success: {result.success}")
    print(f"🔍 Result Answer: {result.answer}")
    
    # Check assertions
    try:
        mock_client.process_vision.assert_called_once_with(image_path)
    except AssertionError as e:
        print(f"❌ FAILURE: process_vision not called correctly: {e}")
        sys.exit(1)
    
    if result.metadata.get("delegated") and result.metadata.get("image_path") == image_path:
        print("✅ SUCCESS: Vision task delegated with correct path!")
    else:
        print("❌ FAILURE: Vision delegation verification failed.")
        print(f"Metadata: {result.metadata}")
        sys.exit(1)

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(test_vision_wiring())
