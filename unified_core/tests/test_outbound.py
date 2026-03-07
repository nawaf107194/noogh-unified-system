import asyncio
import httpx
import logging
import sys
import os

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unified_core.core.actuators import get_actuator_hub

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("outbound_test")

async def test_outbound():
    logger.info("🚀 Starting Controlled Outbound Verification...")
    hub = get_actuator_hub()
    network = hub.network
    
    # Attempt to hit Google
    url = "https://www.google.com"
    logger.info(f"📡 Method: GET | Target: {url}")
    
    # auth is None for internal test (bypass scope check for verification)
    action = await network.http_request(url, "GET", None)
    
    if action.result.value == "success":
        logger.info(f"✅ SUCCESS: Connected to {url}")
        logger.info(f"📊 Status: {action.result_data.get('status')}")
        logger.info(f"📝 Excerpt: {action.result_data.get('body', '')[:100]}...")
    else:
        logger.error(f"❌ FAILED: {action.result.value}")
        logger.error(f"⚠️ Detail: {action.result_data.get('error')}")

if __name__ == "__main__":
    asyncio.run(test_outbound())
