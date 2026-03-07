"""
NOOGH Base Agent Contract

This is the official interface that ALL agents in the NOOGH framework must implement.

This contract is NON-NEGOTIABLE and constitutes a hard requirement
for any component claiming to be a NOOGH agent.

CRITICAL RULES:
1. Agents are WORKERS, not decision makers
2. Agents MUST NOT call tools directly
3. Agents MUST NOT communicate with other agents directly
4. All communication MUST go through MessageBus
5. All tool execution MUST go through UnifiedToolRegistry via IsolationManager
"""

from abc import ABC, abstractmethod
from typing import Set, Dict, Any
from dataclasses import dataclass

from unified_core.orchestration.messages import MessageEnvelope, AgentRole


@dataclass
class AgentResult:
    """
    Standard result format from agent execution.
    
    This is a contract - all agents must return this format.
    """
    success: bool
    task_id: str
    outputs: Dict[str, Any]
    error: str = None
    blocked: bool = False
    resource_usage: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "task_id": self.task_id,
            "outputs": self.outputs,
            "error": self.error,
            "blocked": self.blocked,
            "resource_usage": self.resource_usage or {}
        }


class BaseAgent(ABC):
    """
    Official base class for all NOOGH agents.
    
    This interface is a HARD CONTRACT.
    Any agent that violates it is considered invalid and will be rejected
    by the framework.
    
    CONTRACT GUARANTEES:
    - Pure execution (no side effects outside controlled tools)
    - No direct tool calls
    - No direct inter-agent communication
    - Deterministic behavior
    - Auditable actions
    """
    
    # Required class attributes (must be set by subclass)
    role: AgentRole
    capabilities: Set[str]
    
    def __init__(self, agent_id: str):
        """
        Initialize agent with unique ID.
        
        Args:
            agent_id: Unique identifier for this agent instance
        """
        self.agent_id = agent_id
        self._validate_contract()
    
    def _validate_contract(self):
        """
        Validate that agent implements the contract correctly.
        
        Raises:
            RuntimeError: If contract is violated
        """
        if not hasattr(self, 'role'):
            raise RuntimeError(f"Agent {self.__class__.__name__} missing required 'role' attribute")
        
        if not hasattr(self, 'capabilities'):
            raise RuntimeError(f"Agent {self.__class__.__name__} missing required 'capabilities' attribute")
        
        if not isinstance(self.capabilities, set):
            raise RuntimeError(f"Agent {self.__class__.__name__} 'capabilities' must be a set")
    
    @abstractmethod
    async def handle(self, envelope: MessageEnvelope) -> AgentResult:
        """
        Handle a message from the MessageBus.
        
        CONTRACT RULES:
        1. Must be pure (no side effects outside tools)
        2. Must NOT call tools directly (use IsolationManager)
        3. Must NOT communicate with other agents directly (use MessageBus)
        4. Must return a valid AgentResult
        5. Must handle errors gracefully (never raise unhandled exceptions)
        6. Must respect isolation boundaries
        7. Must log all significant actions
        
        Args:
            envelope: Message envelope from MessageBus
        
        Returns:
            AgentResult with execution outcome
        
        Raises:
            Should NOT raise exceptions - catch and return in AgentResult.error
        """
        raise NotImplementedError(
            f"Agent {self.__class__.__name__} must implement handle() method"
        )
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get agent information for introspection.
        
        Returns:
            Dict with agent metadata
        """
        return {
            "agent_id": self.agent_id,
            "role": self.role.value if hasattr(self.role, 'value') else str(self.role),
            "capabilities": list(self.capabilities),
            "class": self.__class__.__name__
        }
