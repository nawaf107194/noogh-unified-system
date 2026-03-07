"""
NOOGH Multi-Agent Orchestrator

Main orchestration engine for coordinating agents via Message Bus.

CRITICAL SECURITY:
- NO direct tool execution
- ALL via UnifiedToolRegistry
- Message Bus only communication
- Fail-closed on ambiguity
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, List, Optional

from unified_core.orchestration.messages import (
    MessageEnvelope, MessageType, RiskLevel, AgentRole, ToolRequest
)
from unified_core.orchestration.message_bus import get_message_bus
from unified_core.orchestration.task_graph import TaskGraph, TaskNode
from unified_core.orchestration.resource_manager import get_resource_manager
from unified_core.orchestration.isolation_manager import get_isolation_manager
from unified_core.orchestration.risk_policy import ToolRiskClassification, ChainDetector

logger = logging.getLogger("unified_core.orchestration.orchestrator")


class Orchestrator:
    """
    Multi-Agent Kernel Orchestrator.
    
    Responsibilities:
    - Plan validation and DAG construction
    - Resource allocation
    - Agent coordination via Message Bus
    - Security policy enforcement
    - Fail-closed decision making
    """
    
    MAX_TASKS_PER_PLAN = 10
    MAX_TOTAL_TIME_MS = 60000
    
    def __init__(self):
        self.bus = get_message_bus()
        self.resource_mgr = get_resource_manager()
        self.isolation_mgr = get_isolation_manager()
        
        # Registered agents: role → callback
        self._agents: Dict[AgentRole, callable] = {}
        
        # Active plans: trace_id → TaskGraph
        self._active_plans: Dict[str, TaskGraph] = {}
        
        logger.info("✅ Orchestrator initialized")
    
    def register_agent(self, role: AgentRole, callback: callable):
        """Register an agent worker"""
        self._agents[role] = callback
        self.bus.subscribe(f"agent:{role.value}", callback)
        logger.info(f"Registered agent: {role.value}")
    
    async def process_request(
        self,
        request_text: str,
        user_context: Optional[Dict] = None
    ) -> Dict:
        """
        Process user request and create execution plan.
        
        Returns:
            PLAN, REFUSE, or ASK response
        """
        trace_id = str(uuid.uuid4())
        
        # Step 1: Analyze risk
        risk_assessment = self._assess_risk(request_text)
        
        # Step 2: Build plan (would use LLM here in real system)
        # For now, stub implementation
        plan_result = await self._build_plan(request_text, risk_assessment, trace_id)
        
        return plan_result
    
    def _assess_risk(self, request_text: str) -> Dict:
        """Assess overall risk of request"""
        # Simple keyword-based assessment
        # In production, would use LLM + context analysis
        
        request_lower = request_text.lower()
        
        danger_keywords = ["attack", "penetration", "exploit", "network", "delete"]
        restricted_keywords = ["write", "execute", "modify", "test"]
        
        if any(kw in request_lower for kw in danger_keywords):
            overall_risk = RiskLevel.DANGEROUS
            reasons = ["Contains dangerous keywords"]
        elif any(kw in request_lower for kw in restricted_keywords):
            overall_risk = RiskLevel.RESTRICTED
            reasons = ["Contains restricted operation keywords"]
        else:
            overall_risk = RiskLevel.SAFE
            reasons = ["Read-only or analysis operation"]
        
        return {
            "overall_risk": overall_risk,
            "reasons": reasons
        }
    
    async def _build_plan(
        self,
        request_text: str,
        risk_assessment: Dict,
        trace_id: str
    ) -> Dict:
        """Build execution plan (stub)"""
        # This would use LLM to decompose request into tasks
        # For now, return template
        
        return {
            "mode": "ASK",
            "trace_id": trace_id,
            "message": "Plan building requires LLM integration. Please implement agent task decomposition.",
            "required_info": [
                "LLM service for task decomposition",
                "Tool selection logic",
                "Agent role assignment"
            ]
        }
    
    async def execute_plan(self, plan: Dict) -> Dict:
        """
        Execute validated plan.
        
        Args:
            plan: Plan dict with task_graph and messages
        
        Returns:
            Execution results
        """
        trace_id = plan["trace_id"]
        
        # Build TaskGraph
        graph = TaskGraph()
        for node_data in plan["task_graph"]["nodes"]:
            # Convert tool_requests to ToolRequest objects
            tool_requests = [
                ToolRequest(**tr) for tr in node_data.get("tool_requests", [])
            ]
            
            node = TaskNode(
                task_id=node_data["task_id"],
                title=node_data["title"],
                agent_role=node_data["agent_role"],
                risk_level=RiskLevel(node_data["risk_level"]),
                inputs=node_data.get("inputs", []),
                outputs=node_data.get("outputs", []),
                depends_on=node_data.get("depends_on", []),
                tool_requests=tool_requests,
                resource_needs=node_data.get("resource_needs", {})
            )
            graph.add_node(node)
        
        # Validate graph
        is_valid, error = graph.validate()
        if not is_valid:
            logger.error(f"Plan validation failed: {error}")
            return {
                "success": False,
                "error": f"Plan validation failed: {error}",
                "trace_id": trace_id
            }
        
        # Store active plan
        self._active_plans[trace_id] = graph
        
        # Execute tasks in topological order
        execution_order = graph.topological_sort()
        completed_tasks = set()
        results = {}
        
        for task_id in execution_order:
            node = graph.nodes[task_id]
            
            # Acquire resources
            gpu_level = node.resource_needs.get("gpu", "none")
            fs_locks = node.resource_needs.get("fs_lock", [])
            time_budget = node.resource_needs.get("time_budget_ms", 30000)
            
            success, error = await self.resource_mgr.acquire_resources(
                task_id, gpu_level, fs_locks, time_budget
            )
            
            if not success:
                logger.error(f"Resource acquisition failed for {task_id}: {error}")
                results[task_id] = {"success": False, "error": error}
                break
            
            try:
                # Execute task
                task_result = await self._execute_task(node, trace_id)
                results[task_id] = task_result
                completed_tasks.add(task_id)
                
                if not task_result.get("success"):
                    logger.error(f"Task {task_id} failed: {task_result.get('error')}")
                    break
                    
            finally:
                # Release resources
                await self.resource_mgr.release_resources(task_id, gpu_level, fs_locks)
        
        # Cleanup
        del self._active_plans[trace_id]
        
        return {
            "success": len(results) == len(execution_order),
            "results": results,
            "trace_id": trace_id
        }
    
    async def _execute_task(self, node: TaskNode, trace_id: str) -> Dict:
        """Execute single task"""
        logger.info(f"Executing task: {node.task_id} - {node.title}")
        
        task_results = []
        
        # Execute each tool request
        for tool_req in node.tool_requests:
            # Determine isolation
            isolation = self.isolation_mgr.determine_isolation(
                tool_req.tool_name,
                node.risk_level,
                tool_req.isolation if tool_req.isolation != "none" else None
            )
            
            # Execute
            result = await self.isolation_mgr.execute_in_isolation(
                tool_req.tool_name,
                tool_req.arguments,
                isolation,
                tool_req.timeout_ms
            )
            
            task_results.append({
                "tool": tool_req.tool_name,
                "result": result
            })
            
            # Stop if tool failed
            if not result.get("success"):
                return {
                    "success": False,
                    "error":  f"Tool {tool_req.tool_name} failed: {result.get('error')}",
                    "tool_results": task_results
                }
        
        return {
            "success": True,
            "tool_results": task_results
        }


# Global singleton
_orchestrator: Optional[Orchestrator] = None


def get_orchestrator() -> Orchestrator:
    """Get or create global orchestrator"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator
