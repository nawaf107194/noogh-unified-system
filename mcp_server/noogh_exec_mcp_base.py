# mcp_server/noogh_exec_mcp_base.py

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class MCPExecutorBase(ABC):
    """Base class for MCP execution handlers"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._validate_config()
        
    @abstractmethod
    def _validate_config(self) -> None:
        """Validate configuration parameters"""
        pass
        
    @abstractmethod
    def execute_task(self, task_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single MCP task
        Args:
            task_id: Unique identifier for the task
            params: Task parameters
        Returns:
            Execution results
        """
        pass
    
    @abstractmethod
    def get_task_status(self, task_id: str) -> str:
        """
        Get status of a task
        Args:
            task_id: Task identifier
        Returns:
            Task status
        """
        pass
    
    def _log_execution(self, task_id: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Log execution details
        Args:
            task_id: Task identifier
            status: Execution status
            details: Additional execution details
        """
        # Implement logging logic here
        pass