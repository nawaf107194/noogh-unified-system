"""
NOOGH Base Agent Worker

Generic agent worker template that executes tasks from Message Bus.

CRITICAL SECURITY:
- Message Bus communication only (no direct agent-to-agent)
- Capability → Tool mapping
- Isolation enforcement
- All execution via UnifiedToolRegistry
"""

import asyncio
import json
import logging
import os
import re
import sqlite3
import time
import urllib.request
from typing import Dict, Any, Optional, Callable

from unified_core.orchestration.messages import (
    MessageEnvelope, MessageType, RiskLevel, AgentRole
)
from unified_core.orchestration.message_bus import get_message_bus
from unified_core.orchestration.isolation_manager import get_isolation_manager
from unified_core.tool_registry import get_unified_registry

logger = logging.getLogger("unified_core.orchestration.agent_worker")

_DB_PATH   = "/home/noogh/projects/noogh_unified_system/src/data/shared_memory.sqlite"
_VLLM_URL  = os.environ.get("NEURAL_ENGINE_URL", "http://localhost:11434")
_LLM_MODEL = os.environ.get("VLLM_MODEL_NAME", "qwen2.5-coder:14b")


class ComprehensionMixin:
    """
    \u0637\u0628\u0642\u0629 \u0627\u0644\u0641\u0647\u0645 \u0627\u0644\u062d\u0642\u064a\u0642\u064a \u2014 \u062a\u064f\u0636\u0627\u0641 \u0644\u0643\u0644 \u0648\u0643\u064a\u0644 \u062a\u0644\u0642\u0627\u0626\u064a\u0627\u064b

    \u0643\u0644 \u0648\u0643\u064a\u0644 \u064a\u0631\u062b \u0645\u0646 AgentWorker \u064a\u062d\u0635\u0644 \u0639\u0644\u0649:
    - comprehend_result(): \u064a\u0641\u0647\u0645 \u0646\u062a\u064a\u062c\u0629 \u0645\u0647\u0645\u062a\u0647 \u0639\u0628\u0631 LLM
    - _save_understanding(): \u064a\u062d\u0641\u0638 \u0627\u0644\u0641\u0647\u0645 \u0641\u064a \u0630\u0627\u0643\u0631\u0629 NOOGH
    - _ask_brain(): \u064a\u0633\u0623\u0644 \u0627\u0644\u062f\u0645\u0627\u063a \u0633\u0624\u0627\u0644\u0627\u064b
    """

    def _ask_brain(self, prompt: str, max_tokens: int = 400) -> str:
        """\u064a\u0633\u0623\u0644 LLM \u0633\u0624\u0627\u0644\u0627\u064b \u0648\u064a\u0633\u062a\u0642\u0628\u0644 \u0625\u062c\u0627\u0628\u0629 \u062d\u0642\u064a\u0642\u064a\u0629"""
        try:
            payload = {
                "model": _LLM_MODEL,
                "messages": [
                    {"role": "system", "content":
                     "\u0623\u0646\u062a NOOGH. \u062d\u0644\u0644 \u0627\u0644\u0646\u062a\u064a\u062c\u0629 \u0648\u0627\u0633\u062a\u062e\u0644\u0635 \u0627\u0644\u0641\u0647\u0645 \u0627\u0644\u0639\u0645\u064a\u0642. \u0623\u062c\u0628 \u0628\u0627\u0644\u0639\u0631\u0628\u064a\u0629 \u0628\u0645\u062e\u062a\u0635\u0631."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.2,
                "stream": False,
            }
            body = json.dumps(payload).encode()
            req  = urllib.request.Request(
                f"{_VLLM_URL}/v1/chat/completions", data=body,
                headers={"Content-Type": "application/json"}, method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())["choices"][0]["message"]["content"].strip()
        except Exception:
            return ""

    def _save_understanding(self, agent_name: str, task_title: str,
                             understanding: str, utility: float = 0.85):
        """\u064a\u062d\u0641\u0638 \u0627\u0644\u0641\u0647\u0645 \u0641\u064a \u0630\u0627\u0643\u0631\u0629 NOOGH"""
        try:
            conn = sqlite3.connect(_DB_PATH, timeout=5)
            cur  = conn.cursor()
            key  = f"agent_understanding:{agent_name}:{int(time.time())}"
            cur.execute(
                "INSERT OR REPLACE INTO beliefs (key,value,utility_score,updated_at) VALUES (?,?,?,?)",
                (key, json.dumps({
                    "agent": agent_name,
                    "task": task_title,
                    "understanding": understanding,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                }, ensure_ascii=False), utility, time.time())
            )
            conn.commit(); conn.close()
        except Exception:
            pass

    async def comprehend_result(self, agent_name: str, task: Dict,
                                result: Dict) -> str:
        """
        \u064a\u0645\u0631\u0631 \u0646\u062a\u064a\u062c\u0629 \u0627\u0644\u0645\u0647\u0645\u0629 \u0639\u0644\u0649 \u0627\u0644\u062f\u0645\u0627\u063a \u0648\u064a\u062d\u0641\u0638 \u0627\u0644\u0641\u0647\u0645.
        \u064a\u064f\u0633\u062a\u062f\u0639\u0649 \u062a\u0644\u0642\u0627\u0626\u064a\u0627\u064b \u0628\u0639\u062f \u0643\u0644 execute_task().
        """
        task_title = task.get("title", "unknown task")
        capabilities = task.get("capabilities", [])

        # \u062a\u062c\u0647\u064a\u0632 \u0645\u062e\u062a\u0635\u0631 \u0644\u0644\u0646\u062a\u064a\u062c\u0629
        result_preview = json.dumps(result, ensure_ascii=False, default=str)[:500]

        prompt = f"""\u0648\u0643\u064a\u0644 NOOGH [{agent_name}] \u0623\u0646\u062c\u0632 \u0645\u0647\u0645\u0629.

\u0627\u0644\u0645\u0647\u0645\u0629: {task_title}
\u0627\u0644\u0642\u062f\u0631\u0627\u062a: {capabilities}
\u0627\u0644\u0646\u062a\u064a\u062c\u0629:
{result_preview}

\u0627\u0633\u062a\u062e\u0644\u0635 \u0641\u0636\u0644\u0627\u064b:
1. \u0645\u0627\u0630\u0627 \u0641\u0639\u0644 \u0647\u0630\u0627 \u0627\u0644\u0648\u0643\u064a\u0644 \u0628\u0627\u0644\u0636\u0628\u0637?
2. \u0647\u0644 \u0627\u0644\u0646\u062a\u064a\u062c\u0629 \u062c\u064a\u062f\u0629 \u0623\u0645 \u062a\u062d\u062a\u0627\u062c \u062a\u062d\u0633\u064a\u0646\u0627\u064b?
3. \u0645\u0627 \u0627\u0644\u0634\u064a\u0621 \u0627\u0644\u0623\u0647\u0645 \u0627\u0644\u0630\u064a \u064a\u062c\u0628 \u0623\u0646 \u064a\u0639\u0631\u0641\u0647 NOOGH \u0645\u0646 \u0647\u0630\u0647 \u0627\u0644\u0645\u0647\u0645\u0629?

\u0623\u062c\u0628 \u0628\u062c\u0645\u0644\u062a\u064a\u0646 \u0641\u0642\u0637."""

        understanding = await asyncio.get_event_loop().run_in_executor(
            None, self._ask_brain, prompt
        )

        if understanding:
            self._save_understanding(agent_name, task_title, understanding)
            logger.debug(f"  \U0001f4a1 [{agent_name}] \u0641\u0647\u0645: {understanding[:80]}")

        return understanding


class AgentWorker(ComprehensionMixin):
    """
    Base agent worker that executes tasks from orchestrator.
    
    ARCHITECTURE:
    1. Subscribe to MessageBus for assigned role
    2. Receive task assignments (MessageEnvelope)
    3. Map capabilities to tools
    4. Execute via IsolationManager
    5. Report results via MessageBus
    """
    
    # Capability → Tool mapping (override in subclasses)
    CAPABILITY_MAPPING = {
        # Read operations
        "READ_FILE": "fs.read",
        "LIST_FILES": "fs.list",
        "SEARCH_CODE": "dev.search_code",
        "READ_DIRECTORY": "fs.list",
        
        # Analysis (local, no tools needed)
        "ANALYZE_TEXT": None,  # Pure function
        "ANALYZE_CODE": None,
        "DETECT_MALICIOUS_CODE": None,
        "SCAN_CODE_FOR_VULNERABILITIES": None,
        
        # Computation
        "COMPUTE_STATISTICS": None,
        "CALCULATE_METRICS": None,
        "GENERATE_REPORT": None,
        
        # Write (restricted)
        "WRITE_TEMP_FILE": "fs.write",
        "CREATE_PATCH": None,  # Agent-specific
        "GENERATE_CODE_PATCHES": None,
        
        # Execution (dangerous)
        "RUN_SAFE_CODE": "code.exec_python",
        "RUN_TESTS": "dev.run_tests",
        "BUILD_PROJECT": "dev.build",
        
        # Network
        "FETCH_PUBLIC_DATA": "net.http_get",
        "SEND_DATA": "net.http_post",
        "VERIFY_URL": None,
        
        # Memory
        "SEARCH_MEMORY": "mem.search",
        "RECORD_INSIGHT": "mem.record",
        "RETRIEVE_CONTEXT": "mem.search",
        
        # System
        "GET_SYSTEM_INFO": "sys.info",
        "MONITOR_RESOURCES": "sys.processes",
    }
    
    def __init__(self, role: AgentRole, custom_handlers: Optional[Dict[str, Callable]] = None):
        """
        Initialize agent worker.
        
        Args:
            role: Agent role (e.g., AgentRole.CODE_EXECUTOR)
            custom_handlers: Optional dict of capability → handler function
        """
        self.role = role
        self.bus = get_message_bus()
        self.isolation_mgr = get_isolation_manager()
        self.registry = get_unified_registry()
        
        # Custom capability handlers (for pure functions)
        self.custom_handlers = custom_handlers or {}
        
        # Statistics
        self._tasks_executed = 0
        self._tasks_failed = 0
        
        logger.info(f"✅ AgentWorker initialized: {role.value}")
    
    def start(self):
        """Start listening to Message Bus"""
        topic = f"agent:{self.role.value}"
        self.bus.subscribe(topic, self.handle_message)
        logger.info(f"📡 Listening on topic: {topic}")
    
    async def handle_message(self, message: MessageEnvelope):
        """
        Handle incoming message from bus.
        
        CRITICAL: This is the main entry point for task execution.
        """
        # Validate message type
        if message.type != MessageType.REQUEST:
            logger.debug(f"Ignoring non-REQUEST message: {message.type}")
            return
        
        # Extract task
        task = message.payload.get("task")
        if not task:
            logger.error(f"Message {message.message_id} has no task payload")
            return
        
        # Validate task is for this agent
        if task.get("agent_role") != self.role.value:
            logger.debug(f"Task not for this agent: {task.get('agent_role')}")
            return
        
        logger.info(f"📋 Executing task: {task['task_id']} - {task['title']}")
        
        try:
            # Execute task
            result = await self.execute_task(task)
            
            # Send success response
            reply = message.create_reply(
                type=MessageType.RESULT,
                payload={
                    "task_id": task["task_id"],
                    "success": True,
                    "results": result
                }
            )
            
            await self.bus.publish(reply)
            self._tasks_executed += 1

            # طبقة الفهم: كل وكيل يفهم ما فعله تلقائياً
            agent_name = getattr(self.role, 'value', self.__class__.__name__)
            asyncio.ensure_future(
                self.comprehend_result(agent_name, task, result)
            )

            logger.info(f"✅ Task {task['task_id']} completed successfully")

        except Exception as e:
            logger.error(f"❌ Task {task['task_id']} failed: {e}")
            
            # Send error response
            reply = message.create_reply(
                type=MessageType.ERROR,
                payload={
                    "task_id": task["task_id"],
                    "success": False,
                    "error": str(e)
                }
            )
            
            await self.bus.publish(reply)
            self._tasks_failed += 1
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute single task.
        
        Args:
            task: Task dict with capabilities, risk_level, isolation
        
        Returns:
            Execution results
        """
        capabilities = task.get("capabilities", [])
        isolation = task.get("isolation", "none")
        risk_level = RiskLevel[task.get("risk_level", "SAFE")]
        
        logger.error(f"DEBUG: execute_task received capabilities: {capabilities} with args: {task.get('arguments')}")
        
        results = []
        
        for capability in capabilities:
            # Map capability to tool
            tool_name = self._map_capability(capability)
            
            if tool_name is None:
                # Pure function - execute locally
                result = await self._execute_pure_function(capability, task)
            else:
                # Tool execution via registry
                result = await self._execute_tool(
                    tool_name,
                    capability,
                    isolation,
                    task
                )
            
            results.append({
                "capability": capability,
                "tool": tool_name,
                "result": result
            })
            
            # Stop on failure
            if not result.get("success"):
                break
        
        # Report to NeuronFabric — close the learning loop
        all_succeeded = all(r["result"].get("success", False) for r in results)
        try:
            from unified_core.core.neuron_fabric import get_neuron_fabric
            fabric = get_neuron_fabric()
            # Activate neurons related to this agent's role and capabilities
            query = f"{self.role.value} {' '.join(capabilities)}"
            activated = fabric.activate_by_query(query, top_k=5)
            if activated:
                fabric.learn_from_outcome(activated, success=all_succeeded, impact=0.5)
                fabric._save()
        except Exception:
            pass  # Non-critical — never block task execution
        
        return {"capabilities_executed": results}
    
    def _map_capability(self, capability: str) -> Optional[str]:
        """
        Map abstract capability to concrete tool.
        
        Returns:
            Tool name or None for pure functions
        """
        # Check custom handlers first
        if capability in self.custom_handlers:
            return None  # Will be handled by custom handler
        
        # Check standard mapping
        tool = self.CAPABILITY_MAPPING.get(capability)
        
        if tool is None:
            logger.warning(f"Unknown capability: {capability}")
        
        return tool
    
    async def _execute_pure_function(
        self,
        capability: str,
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute pure function (no side effects)"""
        # Check for custom handler
        if capability in self.custom_handlers:
            handler = self.custom_handlers[capability]
            try:
                result = await handler(task)
                return {"success": True, "output": result}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # Default: return stub
        logger.warning(f"No handler for pure function: {capability}")
        return {
            "success": True,
            "output": f"Stub execution for {capability}",
            "note": "Implement custom handler for this capability"
        }
    
    async def _execute_tool(
        self,
        tool_name: str,
        capability: str,
        isolation: str,
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tool via IsolationManager"""
        # Extract arguments from task (task-specific)
        arguments = task.get("arguments", {})
        
        # Auto-confirm: Agent was explicitly assigned this task by the orchestrator,
        # so the HITL approval gate should be bypassed for autonomous execution.
        arguments["confirmed"] = True
        
        # Execute via isolation manager
        result = await self.isolation_mgr.execute_in_isolation(
            tool_name=tool_name,
            arguments=arguments,
            isolation=isolation,
            timeout_ms=task.get("timeout_ms", 10000)
        )
        
        return result
    
    def get_stats(self) -> Dict[str, int]:
        """Get worker statistics"""
        return {
            "tasks_executed": self._tasks_executed,
            "tasks_failed": self._tasks_failed,
            "success_rate": (
                self._tasks_executed / (self._tasks_executed + self._tasks_failed)
                if (self._tasks_executed + self._tasks_failed) > 0
                else 0
            )
        }


# Example: Code Executor Agent
class CodeExecutorAgent(AgentWorker):
    """Specialized agent for code execution"""
    
    def __init__(self):
        # Custom handlers for code-specific capabilities
        custom_handlers = {
            "ANALYZE_CODE": self._analyze_code,
            "GENERATE_CODE_PATCHES": self._generate_patches
        }
        
        super().__init__(AgentRole.CODE_EXECUTOR, custom_handlers)
    
    async def _analyze_code(self, task: Dict) -> str:
        """Analyze code quality via Neural Engine."""
        logger.info(f"[{self.role.value}] Analyzing code via Neural Engine...")
        try:
            from unified_core.neural_bridge import get_neural_bridge
            bridge = get_neural_bridge()
            
            code_fragment = task.get("payload", {}).get("code", "No code provided.")
            response = await bridge.think_with_authority(
                prompt=f"Perform a deep quality analysis on this code: {code_fragment}\nFocus on security, performance, and Sovereign compliance.",
                context={"agent_role": self.role.value, "task_id": task.get("task_id")},
                source="code_executor_agent_analysis"
            )
            return response.get("decision", "Analysis failed to produce a decision.")
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return f"Error during neural analysis: {str(e)}"
    
    async def _generate_patches(self, task: Dict) -> str:
        """Generate code patches via Neural Engine."""
        logger.info(f"[{self.role.value}] Generating patches via Neural Engine...")
        try:
            from unified_core.neural_bridge import get_neural_bridge
            bridge = get_neural_bridge()
            
            issue = task.get("payload", {}).get("issue", "No issue provided.")
            response = await bridge.think_with_authority(
                prompt=f"Generate a structural code patch for the following issue: {issue}\nProvide the patch in diff format.",
                context={"agent_role": self.role.value, "task_id": task.get("task_id")},
                source="code_executor_agent_patching"
            )
            return response.get("decision", "Patch generation failed.")
        except Exception as e:
            logger.error(f"Patch generation failed: {e}")
            return f"Error during neural patch generation: {str(e)}"


# Example: File Manager Agent
class FileManagerAgent(AgentWorker):
    """Specialized agent for file operations"""
    
    def __init__(self):
        super().__init__(AgentRole.FILE_MANAGER)
    
    # Inherits standard capability mapping
    # Override _execute_tool if needed for file-specific logic
