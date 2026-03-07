import sys
import os
sys.path.append("/home/noogh/projects/noogh_unified_system/src")
print("DEBUG: Pre-import", flush=True)
from neural_engine.reasoning_engine import ReasoningEngine
print("DEBUG: Post-import", flush=True)

async def main():
    print("DEBUG: Starting main", flush=True)
    os.environ["NOOGH_ALLOW_UNSTABLE_BACKEND"] = "true"
    try:
        engine = ReasoningEngine(backend="local-gpu")
        print("DEBUG: Engine ready", flush=True)
        query = "كيف حال الرام والمعالج حالياً؟"
        result = await engine.reason({}, query)
        print(f"DEBUG: Result: {result.conclusion}", flush=True)
    except Exception as e:
        print(f"DEBUG: Failure: {e}", flush=True)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
