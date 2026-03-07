from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseSandbox(ABC):
    """Abstract base class for sandbox implementations."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._initialize()
        
    @abstractmethod
    def _initialize(self) -> None:
        """Initialize the sandbox with the given configuration."""
        pass
        
    @abstractmethod
    async def execute_task(self, task_id: str) -> Dict[str, Any]:
        """
        Execute a task within the sandbox environment.
        
        Args:
            task_id: Unique identifier for the task to execute
            
        Returns:
            Dict containing task execution results
        """
        pass
        
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the sandbox.
        
        Returns:
            Dict containing sandbox status information
        """
        pass
        
    @classmethod
    def create_sandbox(cls, config: Dict[str, Any]) -> 'BaseSandbox':
        """
        Factory method to create appropriate sandbox implementation.
        
        Args:
            config: Configuration dict specifying sandbox type and parameters
            
        Returns:
            Instance of BaseSandbox subclass based on configuration
        """
        sandbox_type = config.get('type', 'default')
        if sandbox_type == 'cpu':
            from .cpu_sandbox_impl import CpuSandbox
            return CpuSandbox(config)
        elif sandbox_type == 'gpu':
            from .gpu_sandbox_impl import GpuSandbox
            return GpuSandbox(config)
        else:
            raise ValueError(f"Unsupported sandbox type: {sandbox_type}")