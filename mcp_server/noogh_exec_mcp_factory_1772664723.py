# mcp_server/noogh_exec_mcp_factory.py

from abc import ABC, abstractmethod
from typing import Type, Dict, Any

class MCPExecutor(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._validate_config()
        
    @abstractmethod
    def execute(self) -> Any:
        pass
    
    def _validate_config(self) -> None:
        required_fields = ["endpoint", "timeout"]
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"Missing required config field: {field}")

class MCPExecutorFactory:
    _executors: Dict[str, Type[MCPExecutor]] = {}
    
    @classmethod
    def register(cls, name: str) -> Type[MCPExecutor]:
        def decorator(executor_class: Type[MCPExecutor]) -> Type[MCPExecutor]:
            cls._executors[name] = executor_class
            return executor_class
        return decorator
    
    @classmethod
    def create_executor(cls, name: str, config: Dict[str, Any]) -> MCPExecutor:
        if name not in cls._executors:
            raise ValueError(f"Unknown executor type: {name}")
        return cls._executors[name](config)