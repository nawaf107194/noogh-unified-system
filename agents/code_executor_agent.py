"""
NOOGH Code Executor Agent

Production-ready agent for code execution tasks.

This agent:
- Listens to Message Bus for code execution requests
- Maps capabilities to tools via UnifiedToolRegistry
- Enforces sandbox isolation for all code execution
- Reports results back via Message Bus
"""

import asyncio
import logging
from typing import Dict, Any

from unified_core.orchestration.agent_worker import AgentWorker
from unified_core.orchestration.messages import AgentRole

logger = logging.getLogger("agents.code_executor")


class CodeExecutorAgent(AgentWorker):
    """
    Specialized agent for code execution and analysis.
    
    Capabilities handled:
    - RUN_SAFE_CODE: Execute Python code in sandbox
    - ANALYZE_CODE: Static code analysis
    - GENERATE_CODE_PATCHES: Create code fixes
    - RUN_TESTS: Execute test suites
    - BUILD_PROJECT: Build/compile code
    """
    
    def __init__(self):
        # Define custom handlers for pure functions
        custom_handlers = {
            "ANALYZE_CODE": self._analyze_code,
            "GENERATE_CODE_PATCHES": self._generate_patches,
            "DETECT_MALICIOUS_CODE": self._detect_malicious,
        }
        
        super().__init__(AgentRole.CODE_EXECUTOR, custom_handlers)
        
        # Expand capabilities for this agent to allow full execution
        self.CAPABILITY_MAPPING.update({
            "EXECUTE_SHELL": "proc.run",
            "RUN_COMMAND": "proc.run",
            "INSTALL_PACKAGE": "proc.run",
        })
        
        logger.info("✅ CodeExecutorAgent initialized")
    
    # ========================================================================
    # Custom Capability Handlers (Pure Functions)
    # ========================================================================
    
    async def _analyze_code(self, task: Dict[str, Any]) -> str:
        """
        Analyze code for quality, patterns, and issues.
        
        This is a SAFE operation (no side effects).
        """
        code = task.get("arguments", {}).get("code", "")
        
        # Simple analysis (production would use AST, linters, etc.)
        issues = []
        
        # Check for dangerous patterns
        dangerous_patterns = [
            ("eval(", "Use of eval() is dangerous"),
            ("exec(", "Use of exec() is dangerous"),
            ("os.system(", "Use of os.system() is dangerous"),
            ("subprocess.call(", "Direct subprocess call without validation"),
        ]
        
        for pattern, message in dangerous_patterns:
            if pattern in code:
                issues.append({
                    "type": "SECURITY",
                    "severity": "HIGH",
                    "message": message,
                    "pattern": pattern
                })
        
        # Check for code smells
        if "import *" in code:
            issues.append({
                "type": "QUALITY",
                "severity": "MEDIUM",
                "message": "Wildcard imports reduce code clarity",
                "pattern": "import *"
            })
        
        if len(code.split("\n")) > 100:
            issues.append({
                "type": "QUALITY",
                "severity": "LOW",
                "message": "Code file too long, consider refactoring",
                "pattern": "long_file"
            })
        
        return {
            "analyzed": True,
            "line_count": len(code.split("\n")),
            "issues_found": len(issues),
            "issues": issues
        }
    
    async def _generate_patches(self, task: Dict[str, Any]) -> str:
        """
        Generate code patches based on issues.
        
        This is RESTRICTED (generates code but doesn't execute).
        """
        issues = task.get("arguments", {}).get("issues", [])
        
        patches = []
        
        for issue in issues:
            if issue.get("type") == "SECURITY":
                pattern = issue.get("pattern", "")
                
                # Generate safe alternatives
                if "eval(" in pattern:
                    patches.append({
                        "issue": pattern,
                        "recommendation": "Use ast.literal_eval() for safe evaluation",
                        "example": "import ast\nresult = ast.literal_eval(expr)"
                    })
                elif "os.system(" in pattern:
                    patches.append({
                        "issue": pattern,
                        "recommendation": "Use subprocess.run() with proper validation",
                        "example": "import subprocess\nsubprocess.run(['command'], check=True)"
                    })
        
        return {
            "patches_generated": len(patches),
            "patches": patches
        }
    
    async def _detect_malicious(self, task: Dict[str, Any]) -> str:
        """
        Detect potentially malicious code patterns.
        
        This is SAFE (analysis only).
        """
        code = task.get("arguments", {}).get("code", "")
        
        # Malicious pattern detection
        malicious_patterns = [
            ("__import__('os')", "Dynamic OS import"),
            ("open('/etc/passwd'", "Reading sensitive system files"),
            ("requests.post(", "Potential data exfiltration"),
            ("socket.socket(", "Network socket creation"),
            ("base64.b64decode", "Potential obfuscation"),
        ]
        
        detections = []
        
        for pattern, description in malicious_patterns:
            if pattern in code:
                detections.append({
                    "pattern": pattern,
                    "description": description,
                    "severity": "CRITICAL"
                })
        
        is_malicious = len(detections) > 0
        
        return {
            "is_malicious": is_malicious,
            "confidence": "HIGH" if len(detections) > 2 else "MEDIUM" if len(detections) > 0 else "LOW",
            "detections": detections
        }


# ============================================================================
# Main Entry Point
# ============================================================================

async def main():
    """
    Start the Code Executor Agent.
    
    This is the main entry point for running the agent as a standalone service.
    """
    logger.info("🚀 Starting Code Executor Agent...")
    
    # Create agent
    agent = CodeExecutorAgent()
    
    # Start listening to Message Bus
    agent.start()
    
    logger.info("📡 Agent listening on: agent:code_executor")
    logger.info("✅ Agent ready to receive tasks")
    logger.info("Press Ctrl+C to stop...")
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 Agent stopping...")
        stats = agent.get_stats()
        logger.info(f"📊 Final stats: {stats}")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run agent
    asyncio.run(main())
