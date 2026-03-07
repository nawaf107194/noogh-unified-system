from abc import ABC, abstractmethod
from typing import Dict, Any
import logging
from dataclasses import dataclass

@dataclass
class AgentConfig:
    """Base configuration for agents"""
    name: str
    enabled: bool = True
    logging_level: str = "INFO"
    max_retries: int = 3

class BaseAgent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.logger = logging.getLogger(self.config.name)
        self.logger.setLevel(getattr(logging, self.config.logging_level.upper()))
        
    @abstractmethod
    def run(self) -> None:
        """Main execution method for the agent"""
        pass
    
    def _setup(self) -> None:
        """Common setup tasks"""
        pass
    
    def _teardown(self) -> None:
        """Common cleanup tasks"""
        pass
    
    def _log_error(self, error: Exception) -> None:
        """Log errors with consistent formatting"""
        self.logger.error(f"Error in {self.config.name}: {str(error)}", exc_info=True)
    
    def _retry_operation(self, operation: callable, *args, **kwargs) -> Any:
        """Generic retry mechanism"""
        for attempt in range(self.config.max_retries):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                if attempt == self.config.max_retries - 1:
                    self._log_error(e)
                    raise
                continue