from abc import ABC, abstractmethod
from typing import Any, Optional

class DataProcessorBase(ABC):
    """Abstract base class for data processors with common interface."""
    
    def __init__(self, config: Optional[dict] = None):
        """Initialize processor with optional configuration."""
        self.config = config
        self._validate_config()
        
    @abstractmethod
    def _validate_config(self) -> None:
        """Validate configuration parameters. To be implemented by subclasses."""
        pass
        
    @abstractmethod
    def load(self, data_source: str) -> Any:
        """Load data from source. To be implemented by subclasses."""
        pass
        
    @abstractmethod
    def transform(self, data: Any) -> Any:
        """Transform data. To be implemented by subclasses."""
        pass
        
    @abstractmethod
    def serialize(self, data: Any, output_path: str) -> None:
        """Serialize data to output path. To be implemented by subclasses."""
        pass
        
    def process(self, data_source: str, output_path: str) -> None:
        """Full processing pipeline."""
        data = self.load(data_source)
        transformed_data = self.transform(data)
        self.serialize(transformed_data, output_path)