"""NOOGH LogAnalyzerAgent — Auto-generated"""

import asyncio
import logging
from typing import Dict, Any
from collections import Counter

from unified_core.orchestration.agent_worker import AgentWorker
from unified_core.orchestration.messages import AgentRole

logger = logging.getLogger("agents.log_analyzer")


class LogAnalyzerAgent(AgentWorker):
    """System log analysis agent."""
    
    def __init__(self):
        custom_handlers = {
            "ANALYZE_LOGS": self._analyze_logs,
            "DETECT_ERROR_PATTERNS": self._detect_patterns,
        }
        role = AgentRole("log_analyzer")
        super().__init__(role, custom_handlers)
        logger.info("✅ LogAnalyzerAgent initialized")
    
    async def _analyze_logs(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and analyze recent log entries."""
        try:
            arguments = task.get("arguments", {})
            log_path = arguments.get("log_path", "/var/log/syslog")
            lines = arguments.get("lines", 100)
            
            import asyncio
            process = await asyncio.create_subprocess_exec(
                "tail", "-n", str(lines), log_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            try:
                stdout_bytes, _ = await asyncio.wait_for(process.communicate(), timeout=10.0)
            except asyncio.TimeoutError:
                process.kill()
                return {"success": False, "error": "Command timed out"}
                
            content = stdout_bytes.decode('utf-8', 'replace')
            
            error_count = content.lower().count("error")
            warning_count = content.lower().count("warning")
            
            return {
                "success": True,
                "total_lines": len(content.splitlines()),
                "errors": error_count,
                "warnings": warning_count,
                "health": "good" if error_count < 5 else "degraded"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _detect_patterns(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Find recurring error patterns."""
        try:
            arguments = task.get("arguments", {})
            log_lines = arguments.get("log_lines", [])
            
            errors = [l for l in log_lines if "error" in l.lower()]
            patterns = Counter()
            for err in errors:
                key = err.strip()[:50]
                patterns[key] += 1
            
            recurring = [
                {"pattern": p, "count": c}
                for p, c in patterns.most_common(10)
                if c > 1
            ]
            
            return {"success": True, "recurring_errors": recurring}
        except Exception as e:
            return {"success": False, "error": str(e)}


async def main():
    agent = LogAnalyzerAgent()
    agent.start()
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    import sys
    if "--report" in sys.argv:
        import json
        async def run_report():
            agent = object.__new__(LogAnalyzerAgent)
            res1 = await agent._analyze_logs({"arguments": {"log_path": "/home/noogh/projects/noogh_unified_system/src/logs/orchestrator.log", "lines": 200}})
            print(json.dumps({"logs": res1}, indent=2))
        asyncio.run(run_report())
        sys.exit(0)

    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
