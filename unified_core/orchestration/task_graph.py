"""
NOOGH Task Graph (DAG)

DAG validation and topological sorting for task execution.

SECURITY: Validates task dependencies to prevent cycles and dangerous chaining patterns.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from unified_core.orchestration.messages import RiskLevel, ToolRequest

logger = logging.getLogger("unified_core.orchestration.task_graph")


@dataclass
class TaskNode:
    """Single task node in execution DAG"""
    task_id: str
    title: str
    agent_role: str
    risk_level: RiskLevel
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    tool_requests: List[ToolRequest] = field(default_factory=list)
    resource_needs: Dict[str, any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "agent_role": self.agent_role,
            "risk_level": self.risk_level.value,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "depends_on": self.depends_on,
            "tool_requests": [tr.to_dict() for tr in self.tool_requests],
            "resource_needs": self.resource_needs
        }


class TaskGraph:
    """
    DAG for orchestrated task execution.
    
    SECURITY CRITICAL:
    - Prevents cycles
    - Detects dangerous chaining patterns
    - Validates resource constraints
    """
    
    def __init__(self):
        self.nodes: Dict[str, TaskNode] = {}
        self._validated = False
    
    def add_node(self, node: TaskNode):
        """Add task node to graph"""
        if node.task_id in self.nodes:
            raise ValueError(f"Duplicate task_id: {node.task_id}")
        self.nodes[node.task_id] = node
        self._validated = False
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate graph structure and security constraints.
        
        Returns:
            (is_valid, error_message)
        """
        # Check 1: All dependencies exist
        for node in self.nodes.values():
            for dep_id in node.depends_on:
                if dep_id not in self.nodes:
                    return False, f"Task {node.task_id} depends on non-existent task {dep_id}"
        
        # Check 2: No cycles
        if self._has_cycle():
            return False, "Graph contains cycles"
        
        # Check 3: Dangerous chaining patterns
        dangerous_chain = self._detect_dangerous_chains()
        if dangerous_chain:
            return False, f"Dangerous tool chaining detected: {dangerous_chain}"
        
        # Check 4: Max tasks limit (security: prevent DoS)
        if len(self.nodes) > 10:
            return False, f"Too many tasks ({len(self.nodes)}). Max 10 per plan."
        
        self._validated = True
        return True, None
    
    def _has_cycle(self) -> bool:
        """Check for cycles using DFS"""
        visited = set()
        rec_stack = set()
        
        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            node = self.nodes[node_id]
            for dep_id in node.depends_on:
                if dep_id not in visited:
                    if dfs(dep_id):
                        return True
                elif dep_id in rec_stack:
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        for node_id in self.nodes:
            if node_id not in visited:
                if dfs(node_id):
                    return True
        
        return False
    
    def _detect_dangerous_chains(self) -> Optional[str]:
        """
        Detect dangerous tool chaining patterns.
        
        Blocked patterns:
        1. write → exec (write malicious code then execute)
        2. read_secrets → network (exfiltrate secrets)
        3. download → exec (download malware then run)
        """
        DANGEROUS_PATTERNS = [
            (["fs.write", "code.exec_python"], "write → exec"),
            (["fs.write", "proc.run"], "write → shell"),
            (["mem.search", "net.http_post"], "memory_exfiltration"),
            (["net.http_get", "code.exec_python"], "download → exec"),
        ]
        
        # Build execution order
        order = self.topological_sort()
        if not order:
            return "Cannot determine execution order"
        
        # Check each pattern
        for pattern_tools, pattern_name in DANGEROUS_PATTERNS:
            # Find if pattern tools appear in sequence
            pattern_indices = []
            for tool_name in pattern_tools:
                for i, task_id in enumerate(order):
                    node = self.nodes[task_id]
                    for tool_req in node.tool_requests:
                        if tool_req.tool_name == tool_name:
                            pattern_indices.append(i)
                            break
            
            # Check if found in sequence
            if len(pattern_indices) == len(pattern_tools):
                if pattern_indices == sorted(pattern_indices):
                    return pattern_name
        
        return None
    
    def topological_sort(self) -> Optional[List[str]]:
        """
        Return tasks in execution order (topological sort).
        
        Note: Call validate() before calling this method.
        
        Returns:
            List of task_ids in execution order, or None if invalid
        """
        # Kahn's algorithm
        # in_degree = number of dependencies (incoming edges)
        in_degree = {node_id: len(node.depends_on) for node_id, node in self.nodes.items()}
        
        # Start with tasks that have no dependencies
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            node_id = queue.pop(0)
            result.append(node_id)
            
            # Find tasks that depend on this completed task
            for other_id, other_node in self.nodes.items():
                if node_id in other_node.depends_on:
                    in_degree[other_id] -= 1
                    if in_degree[other_id] == 0:
                        queue.append(other_id)
        
        if len(result) != len(self.nodes):
            logger.error("Topological sort failed - graph has cycles")
            return None
        
        return result
    
    def get_executable_tasks(self, completed: Set[str]) -> List[str]:
        """
        Get tasks that can be executed now (all dependencies satisfied).
        
        Args:
            completed: Set of completed task_ids
        
        Returns:
            List of task_ids ready to execute
        """
        executable = []
        for task_id, node in self.nodes.items():
            if task_id in completed:
                continue
            
            # Check if all dependencies are completed
            if all(dep_id in completed for dep_id in node.depends_on):
                executable.append(task_id)
        
        return executable
