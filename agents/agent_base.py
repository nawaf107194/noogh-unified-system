from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class AgentConfig:
    """Configuration for agents"""
    name: str
    enabled: bool = True
    parameters: Dict[str, Any] = {}
    
class AgentBase(ABC):
    """Abstract base class for all agents"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.status = "stopped"
        self.last_run_time = None
        
    @abstractmethod
    def setup(self) -> None:
        """Initialize agent resources"""
        pass
        
    @abstractmethod
    def execute(self) -> None:
        """Main execution logic"""
        pass
        
    @abstractmethod
    def teardown(self) -> None:
        """Clean up resources"""
        pass
    
    def start(self) -> None:
        """Start agent execution"""
        if self.status != "running":
            self.setup()
            self.execute()
            self.status = "running"
            
    def stop(self) -> None:
        """Stop agent execution"""
        if self.status == "running":
            self.teardown()
            self.status = "stopped"
    
    @property
    def is_running(self) -> bool:
        """Check if agent is running"""
        return self.status == "running"
    
    @classmethod
    def from_config(cls, config_path: str) -> 'AgentBase':
        """Create agent from configuration file"""
        # Implement config loading logic
        pass