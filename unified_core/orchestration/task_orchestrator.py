"""
NOOGH Multi-Agent Task Orchestrator
=====================================
Coordinates tasks across multiple agents via the MessageBus.

Features:
- Task graphs with dependencies
- Parallel execution where possible
- Result aggregation
- Timeout and fallback handling
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field

logger = logging.getLogger("unified_core.orchestration.task_orchestrator")


@dataclass
class TaskNode:
    """A single task in the execution graph."""
    task_id: str
    agent_role: str       # Which agent handles this
    capability: str       # Which capability to invoke
    arguments: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)  # task_ids
    timeout_ms: int = 30000
    result: Optional[Dict[str, Any]] = None
    status: str = "pending"  # pending, running, done, failed, skipped
    started_at: float = 0.0
    completed_at: float = 0.0


@dataclass 
class TaskGraph:
    """A directed acyclic graph of tasks."""
    graph_id: str = field(default_factory=lambda: f"graph_{uuid.uuid4().hex[:8]}")
    name: str = ""
    tasks: Dict[str, TaskNode] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    
    def add_task(
        self,
        agent_role: str,
        capability: str,
        arguments: Dict[str, Any] = None,
        depends_on: List[str] = None,
        timeout_ms: int = 30000,
        task_id: str = None,
    ) -> str:
        """Add a task to the graph. Returns the task_id."""
        tid = task_id or f"task_{len(self.tasks)}_{agent_role}"
        node = TaskNode(
            task_id=tid,
            agent_role=agent_role,
            capability=capability,
            arguments=arguments or {},
            depends_on=depends_on or [],
            timeout_ms=timeout_ms,
        )
        self.tasks[tid] = node
        return tid
    
    def get_ready_tasks(self) -> List[TaskNode]:
        """Get tasks whose dependencies are all satisfied."""
        ready = []
        for task in self.tasks.values():
            if task.status != "pending":
                continue
            deps_met = all(
                self.tasks[dep].status == "done"
                for dep in task.depends_on
                if dep in self.tasks
            )
            deps_failed = any(
                self.tasks[dep].status == "failed"
                for dep in task.depends_on
                if dep in self.tasks
            )
            if deps_failed:
                task.status = "skipped"
                continue
            if deps_met:
                ready.append(task)
        return ready
    
    def is_complete(self) -> bool:
        return all(t.status in ("done", "failed", "skipped") for t in self.tasks.values())
    
    def summary(self) -> Dict[str, Any]:
        statuses = {}
        for t in self.tasks.values():
            statuses[t.status] = statuses.get(t.status, 0) + 1
        return {
            "graph_id": self.graph_id,
            "name": self.name,
            "total_tasks": len(self.tasks),
            "statuses": statuses,
            "complete": self.is_complete(),
        }


class TaskOrchestrator:
    """
    Executes task graphs across multiple agents.
    
    Uses the MessageBus for agent communication.
    """
    
    def __init__(self, message_bus=None):
        if message_bus is None:
            from .message_bus import get_message_bus
            message_bus = get_message_bus()
        self.bus = message_bus
        self._active_graphs: Dict[str, TaskGraph] = {}
        self._completed_graphs: List[Dict[str, Any]] = []
        logger.info("✅ TaskOrchestrator initialized")
    
    async def execute_graph(self, graph: TaskGraph) -> Dict[str, Any]:
        """
        Execute a task graph, respecting dependencies.
        
        Tasks without dependencies run in parallel.
        Tasks with dependencies wait for their prerequisites.
        """
        self._active_graphs[graph.graph_id] = graph
        start_time = time.time()
        
        logger.info(f"📋 Executing graph '{graph.name}' ({len(graph.tasks)} tasks)")
        
        max_iterations = len(graph.tasks) + 5  # Safety limit
        iteration = 0
        
        while not graph.is_complete() and iteration < max_iterations:
            iteration += 1
            ready = graph.get_ready_tasks()
            
            if not ready:
                if graph.is_complete():
                    break
                # Deadlock detection
                pending = [t for t in graph.tasks.values() if t.status == "pending"]
                if pending:
                    logger.error(f"⚠️ Deadlock: {len(pending)} tasks stuck")
                    for t in pending:
                        t.status = "failed"
                        t.result = {"error": "deadlock"}
                    break
                break
            
            # Execute ready tasks in parallel
            tasks_coros = [self._execute_task(t) for t in ready]
            await asyncio.gather(*tasks_coros, return_exceptions=True)
        
        elapsed = round(time.time() - start_time, 1)
        
        # Build result
        result = {
            "graph_id": graph.graph_id,
            "name": graph.name,
            "elapsed_seconds": elapsed,
            "summary": graph.summary(),
            "results": {
                tid: {
                    "status": t.status,
                    "result": t.result,
                    "agent": t.agent_role,
                    "capability": t.capability,
                }
                for tid, t in graph.tasks.items()
            },
        }
        
        # Move to completed
        del self._active_graphs[graph.graph_id]
        self._completed_graphs.append(result)
        if len(self._completed_graphs) > 50:
            self._completed_graphs.pop(0)
        
        logger.info(f"✅ Graph '{graph.name}' complete: {graph.summary()} ({elapsed}s)")
        return result
    
    async def _execute_task(self, task: TaskNode):
        """Execute a single task by sending it to the appropriate agent."""
        task.status = "running"
        task.started_at = time.time()
        
        try:
            from .messages import MessageEnvelope, MessageType, RiskLevel
            
            msg = MessageEnvelope(
                sender="orchestrator",
                receiver=f"agent:{task.agent_role}",
                type=MessageType.TASK,
                risk=RiskLevel.LOW,
                payload={
                    "capability": task.capability,
                    "arguments": task.arguments,
                    "task_id": task.task_id,
                },
            )
            
            reply = await self.bus.request_reply(msg, timeout_ms=task.timeout_ms)
            
            if reply and reply.payload:
                task.result = reply.payload
                task.status = "done" if reply.payload.get("success") else "failed"
            else:
                task.result = {"error": "timeout or no reply"}
                task.status = "failed"
                
        except Exception as e:
            task.result = {"error": str(e)}
            task.status = "failed"
            logger.error(f"Task {task.task_id} failed: {e}")
        
        task.completed_at = time.time()
        elapsed = round(task.completed_at - task.started_at, 1)
        logger.info(f"  {'✅' if task.status == 'done' else '❌'} {task.task_id} ({elapsed}s)")
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "active_graphs": len(self._active_graphs),
            "completed_graphs": len(self._completed_graphs),
        }


# Convenience builders for common patterns

def build_health_check_graph() -> TaskGraph:
    """Build a multi-agent health check graph."""
    g = TaskGraph(name="system_health_check")
    
    # These run in parallel (no dependencies)
    g.add_task("health_monitor", "MONITOR_HEALTH", task_id="health")
    g.add_task("log_analyzer", "ANALYZE_LOGS", 
               arguments={"lines": 100}, task_id="logs")
    g.add_task("dependency_auditor", "AUDIT_DEPS", task_id="deps")
    
    # This runs after health + logs complete
    g.add_task("web_researcher", "WEB_SEARCH",
               arguments={"query": "system monitoring best practices"},
               depends_on=["health", "logs"],
               task_id="research")
    
    return g

def build_pre_evolution_check() -> TaskGraph:
    """Build a pre-evolution safety check graph."""
    g = TaskGraph(name="pre_evolution_check")
    
    # Step 1: Run tests + audit deps in parallel
    g.add_task("test_runner", "RUN_TESTS", task_id="tests")
    g.add_task("dependency_auditor", "CHECK_VULNERABILITIES", task_id="vulns")
    
    # Step 2: Health check after tests pass
    g.add_task("health_monitor", "CHECK_SERVICES",
               depends_on=["tests"],
               task_id="services")
    
    return g


# Singleton
_orchestrator: Optional[TaskOrchestrator] = None

def get_task_orchestrator() -> TaskOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = TaskOrchestrator()
    return _orchestrator
