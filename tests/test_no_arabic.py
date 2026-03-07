import sys
print("DEBUG: Starting test_no_arabic.py", flush=True)
import asyncio
import os
import logging

sys.path.append("/home/noogh/projects/noogh_unified_system/src")
from neural_engine.reasoning_engine import ReasoningEngine

async def test():
    print("DEBUG: Starting test()", flush=True)
    os.environ["NOOGH_ALLOW_UNSTABLE_BACKEND"] = "true"
    engine = ReasoningEngine(backend="local-gpu")
    print("DEBUG: Engine ready", flush=True)
    query = "List the files in the current directory"
    print(f"DEBUG: Reasoning about: {query}", flush=True)
    result = await engine.reason({}, query)
    print(f"DEBUG: Result conclusion: {result.conclusion}", flush=True)

if __name__ == "__main__":
    asyncio.run(test())
