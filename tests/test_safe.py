import sys
import asyncio
import os
import logging

print("DEBUG: test_safe.py started", flush=True)

os.environ["NOOGH_ALLOW_UNSTABLE_BACKEND"] = "true"

try:
    sys.path.append("/home/noogh/projects/noogh_unified_system/src")
    from neural_engine.reasoning_engine import ReasoningEngine
    print("DEBUG: ReasoningEngine imported", flush=True)
except Exception as e:
    print(f"DEBUG: Import failure: {e}", flush=True)
    sys.exit(1)

async def test():
    print("DEBUG: Starting test coroutine", flush=True)
    try:
        engine = ReasoningEngine(backend="local-gpu")
        print("DEBUG: Engine initialized", flush=True)
        query = "كيف حال الرام والمعالج حالياً؟"
        print(f"DEBUG: Querying: {query}", flush=True)
        result = await engine.reason({}, query)
        print("DEBUG: Reasoning complete", flush=True)
        print(f"DEBUG: Conclusion: {result.conclusion}", flush=True)
    except Exception as e:
        print(f"DEBUG: Runtime failure: {e}", flush=True)

if __name__ == "__main__":
    asyncio.run(test())
