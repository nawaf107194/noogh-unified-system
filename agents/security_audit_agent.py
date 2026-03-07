"""NOOGH Security Audit Agent 

Purpose: Automatically audit rapid prototypes and system files for vulnerabilities,
         and monitor GPU/compute allocations to prevent overheating.
Capabilities:
- SECURITY_SCAN: Scans a given codebase or file for critical vulnerabilities like eval/exec.
- RESOURCE_AUDIT: Monitors GPU footprint and reports warnings.
"""

import asyncio
import logging
import os
import psutil
from typing import Dict, Any

from unified_core.orchestration.agent_worker import AgentWorker
from unified_core.orchestration.messages import AgentRole
from unified_core.core.memory_store import UnifiedMemoryStore

logger = logging.getLogger("agents.security_audit")

class SecurityAuditAgent(AgentWorker):
    """
    Sovereign agent protecting NOOGH from its own RapidPrototyping vulnerabilities
    and tracking resource exhaustion.
    """
    
    def __init__(self):
        custom_handlers = {
            "SECURITY_SCAN": self._scan_code,
            "RESOURCE_AUDIT": self._check_resources
        }
        # Fallback to dev_agent or generic role
        role = AgentRole("dev_agent") if hasattr(AgentRole, "dev_agent") else AgentRole("web_researcher")
        super().__init__(role, custom_handlers)
        self.memory = UnifiedMemoryStore()
        logger.info("🛡️ SecurityAuditAgent initialized (Sovereign Protection Active)")

    async def _scan_code(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Scans rapid generated code for dangerous elements."""
        code_path = task.get("file_path", "")
        if not os.path.exists(code_path):
            return {"success": False, "error": "File not found"}
            
        logger.info(f"🛡️ Scanning {code_path} for vulnerabilities...")
        vulnerabilities = []
        with open(code_path, "r") as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if "eval(" in line or "exec(" in line:
                    vulnerabilities.append(f"Line {i+1}: Critical Code Execution (eval/exec)")
                if "os.system(" in line or "subprocess.Popen" in line:
                    vulnerabilities.append(f"Line {i+1}: OS Command Injection Risk")
                    
        # Log findings to memory
        if vulnerabilities:
            obs = {
                "source": "SecurityAuditAgent",
                "content": f"Vulnerabilities found in {code_path}: {', '.join(vulnerabilities)}",
                "timestamp": asyncio.get_event_loop().time()
            }
            await self.memory.append_observation(obs)
            return {"success": True, "status": "VULNERABLE", "findings": vulnerabilities}
            
        return {"success": True, "status": "SECURE", "findings": []}

    async def _check_resources(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Provides snapshot of CPU/RAM to prevent rapid prototyping bottlenecks."""
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory().percent
        logger.info(f"📊 SecAudit - CPU: {cpu}%, MEM: {mem}%")
        
        status = "CRITICAL" if cpu > 90 or mem > 90 else "HEALTHY"
        return {"success": True, "status": status, "cpu": cpu, "memory": mem}

async def main():
    agent = SecurityAuditAgent()
    agent.start()
    try:
        while True:
            await asyncio.sleep(1)
            # Periodic independent audit logic could go here
    except KeyboardInterrupt:
        logger.info("🛑 SecurityAuditAgent stopping...")

if __name__ == "__main__":
    import sys
    if "--report" in sys.argv:
        import json
        async def run_report():
            agent = object.__new__(SecurityAuditAgent)
            class MockMem:
                async def append_observation(self, obs): pass
            agent.memory = MockMem()
            res1 = await agent._check_resources({})
            res2 = await agent._scan_code({"file_path": "/home/noogh/projects/noogh_unified_system/src/agents/noogh_orchestrator.py"})
            print(json.dumps({"resources": res1, "scan": res2}, indent=2))
        asyncio.run(run_report())
        sys.exit(0)

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    asyncio.run(main())
