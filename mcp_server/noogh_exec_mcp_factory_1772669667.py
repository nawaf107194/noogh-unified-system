from abc import ABC, abstractmethod
from typing import Type

class NooGHExecutorFactory(ABC):
    """Abstract Factory interface for creating MCP executor components"""
    
    @abstractmethod
    def create_executor(self) -> Type['MCPExecutor']:
        """Create a new MCP executor instance"""
        pass
    
    @abstractmethod
    def create_strategy(self) -> Type['ExecutionStrategy']:
        """Create a new execution strategy instance"""
        pass
    
    @abstractmethod
    def create_config(self) -> dict:
        """Create default configuration for executor"""
        pass

class DefaultExecutorFactory(NooGHExecutorFactory):
    """Concrete factory for default MCP executor implementation"""
    
    def create_executor(self) -> Type['MCPExecutor']:
        from .noogh_exec_mcp_base import BaseMCPExecutor
        return BaseMCPExecutor
    
    def create_strategy(self) -> Type['ExecutionStrategy']:
        from .noogh_exec_mcp_base import DefaultExecutionStrategy
        return DefaultExecutionStrategy
    
    def create_config(self) -> dict:
        return {
            'execution_mode': 'default',
            'timeout': 60,
            'max_retries': 3
        }

class EnhancedExecutorFactory(NooGHExecutorFactory):
    """Concrete factory for enhanced MCP executor implementation"""
    
    def create_executor(self) -> Type['MCPExecutor']:
        from .noogh_exec_mcp_1771795578 import EnhancedMCPExecutor
        return EnhancedMCPExecutor
    
    def create_strategy(self) -> Type['ExecutionStrategy']:
        from .noogh_exec_mcp_1771795578 import OptimizedExecutionStrategy
        return OptimizedExecutionStrategy
    
    def create_config(self) -> dict:
        return {
            'execution_mode': 'enhanced',
            'timeout': 30,
            'max_retries': 5
        }