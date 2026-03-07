import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

# Ensure project root is in path
sys.path.insert(0, "/home/noogh/projects/noogh_unified_system/src")
load_dotenv("/home/noogh/projects/noogh_unified_system/src/.env")

from unified_core.neural_bridge import get_neural_bridge, NeuralRequest

async def test_bridge():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("test_bridge")
    
    logger.info("Connecting to NeuralBridge...")
    bridge = get_neural_bridge()
    
    request = NeuralRequest(query="Hello, are you operational?", urgency=0.1)
    logger.info("Sending test request...")
    try:
        response = await bridge.think_with_authority(request)
        if response.success:
            logger.info(f"✅ Success! Response: {response.content}")
        else:
            logger.error(f"❌ Failed! Error: {response.error}")
    except Exception as e:
        logger.error(f"💥 Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_bridge())
