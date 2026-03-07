import sys
print("DEBUG: Starting test_model_integration.py", flush=True)
import asyncio
import os
import logging

# Setup logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add src to sys.path
sys.path.append("/home/noogh/projects/noogh_unified_system/src")

from neural_engine.reasoning_engine import ReasoningEngine

async def test_integration():
    print("🚀 Testing NOOGH Tool Model Integration...")
    
    # Initialize engine with local-gpu (it will use ModelAuthority)
    engine = ReasoningEngine(backend="local-gpu")
    
    test_queries = [
        "كيف حال الرام والمعالج حالياً؟",
        "ls -la",
        "tell me a joke",
        "ما هو وقت النظام؟"
    ]
    
    for query in test_queries:
        print(f"\n--- Testing Query: {query} ---", flush=True)
        try:
            # We use context {} for simplicity
            result = await engine.reason({}, query)
            print(f"Result Conclusion: {result.conclusion}", flush=True)
            print(f"Confidence: {result.confidence}", flush=True)
            if result.raw_response:
                print(f"Raw Response: {result.raw_response.strip()}", flush=True)
        except Exception as e:
            print(f"❌ Error during test: {e}", flush=True)

if __name__ == "__main__":
    asyncio.run(test_integration())
