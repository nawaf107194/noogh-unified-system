import sys
print("DEBUG: Layer 1 - Entry", flush=True)
import asyncio
import os
import logging

print("DEBUG: Layer 2 - Imports of stdlib done", flush=True)

# Add src to sys.path
sys.path.append("/home/noogh/projects/noogh_unified_system/src")

from neural_engine.reasoning_engine import ReasoningEngine
print("DEBUG: Layer 3 - ReasoningEngine import done", flush=True)

async def test_integration():
    print("DEBUG: Layer 4 - test_integration() started", flush=True)
    try:
        engine = ReasoningEngine(backend="local-gpu")
        print("DEBUG: Layer 5 - ReasoningEngine initialized", flush=True)
    except Exception as e:
        print(f"DEBUG: Error during initialization: {e}", flush=True)
        return

    query = "كيف حال الرام والمعالج حالياً؟"
    print(f"DEBUG: Layer 6 - Testing query: {query}", flush=True)
    try:
        result = await engine.reason({}, query)
        print(f"DEBUG: Layer 7 - Result Conclusion: {result.conclusion}", flush=True)
        if result.raw_response:
             print(f"DEBUG: Raw Response: {result.raw_response.strip()}", flush=True)
    except Exception as e:
        print(f"DEBUG: Error during reason(): {e}", flush=True)

if __name__ == "__main__":
    print("DEBUG: Layer 8 - Calling asyncio.run()", flush=True)
    try:
        asyncio.run(test_integration())
    except Exception as e:
        print(f"DEBUG: asyncio.run failed: {e}", flush=True)
    print("DEBUG: Layer 9 - Finished", flush=True)
