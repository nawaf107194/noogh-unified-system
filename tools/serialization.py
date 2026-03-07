import json
import csv
import io
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
try:
    import yaml
except ImportError:
    yaml = None

class SerializationStrategy(ABC):
    """Abstract base class for serialization strategies"""
    @abstractmethod
    def serialize(self, data: Any) -> str:
        """Serializes data to a string"""
        pass

    @abstractmethod
    def deserialize(self, data_str: str) -> Any:
        """Deserializes string to data"""
        pass

class JSONSerializationStrategy(SerializationStrategy):
    """JSON serialization strategy"""
    def serialize(self, data: Any) -> str:
        return json.dumps(data, indent=4)

    def deserialize(self, data_str: str) -> Any:
        return json.loads(data_str)

class YAMLSerializationStrategy(SerializationStrategy):
    """YAML serialization strategy"""
    def serialize(self, data: Any) -> str:
        if yaml:
            return yaml.safe_dump(data, default_flow_style=False)
        raise ImportError("PyYAML is not installed.")

    def deserialize(self, data_str: str) -> Any:
        if yaml:
            return yaml.safe_load(data_str)
        raise ImportError("PyYAML is not installed.")

class CSVSerializationStrategy(SerializationStrategy):
    """CSV serialization strategy (for lists of dicts)"""
    def serialize(self, data: List[Dict[str, Any]]) -> str:
        if not data: return ""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()

    def deserialize(self, data_str: str) -> List[Dict[str, Any]]:
        input_data = io.StringIO(data_str)
        reader = csv.DictReader(input_data)
        return [row for row in reader]

class SerializationContext:
    """Context that uses a SerializationStrategy"""
    def __init__(self, strategy: SerializationStrategy):
        self._strategy = strategy

    def set_strategy(self, strategy: SerializationStrategy):
        self._strategy = strategy

    def serialize(self, data: Any) -> str:
        return self._strategy.serialize(data)

    def deserialize(self, data_str: str) -> Any:
        return self._strategy.deserialize(data_str)
