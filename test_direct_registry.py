import asyncio
import logging
import json
from unified_core.orchestration.isolation_manager import get_isolation_manager
from unified_core.sandbox_service import get_sandbox_service

logging.basicConfig(level=logging.INFO)

async def run_test():
    print("STEP: get_isolation_manager")
    iso = get_isolation_manager()
    
    # Bypass registry entirely, call SandboxService direct
    print("STEP: get_sandbox_service")
    sandbox = get_sandbox_service()
    
    print("STEP: Executing proc.run via SandboxService...")
    res = await sandbox.execute("proc.run", {
        "command": "echo 'SUCCESS' > /tmp/noogh_test_alive.txt"
    }, timeout_ms=5000)
    
    print("STEP: Result received")
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    asyncio.run(run_test())
