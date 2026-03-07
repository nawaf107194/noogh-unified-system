import sys
print("DEBUG: Starting minimal_test.py", flush=True)
import asyncio
import os
import logging
print("DEBUG: Basic imports successful", flush=True)

try:
    from neural_engine.reasoning_engine import ReasoningEngine
    print("DEBUG: ReasoningEngine import successful", flush=True)
except Exception as e:
    print(f"DEBUG: ReasoningEngine import FAILED: {e}", flush=True)
    sys.exit(1)

async def main():
    print("DEBUG: Inside main()", flush=True)

if __name__ == "__main__":
    print("DEBUG: Calling asyncio.run()", flush=True)
    asyncio.run(main())
    print("DEBUG: Finished", flush=True)
