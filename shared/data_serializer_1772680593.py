from abc import ABC, abstractmethod
from typing import Dict, Any

class SerializationStrategy(ABC):
    """Abstract base class for different serialization strategies"""
    
    @abstractmethod
    def serialize(self, data: Dict) -> str:
        """Serialize data to a string representation"""
        pass
    
    @abstractmethod
    def deserialize(self, data_str: str) -> Dict:
        """Deserialize a string back to a dictionary"""
        pass

class JSONSerializationStrategy(SerializationStrategy):
    """Concrete strategy for JSON serialization"""
    
    def serialize(self, data: Dict) -> str:
        import json
        return json.dumps(data)
    
    def deserialize(self, data_str: str) -> Dict:
        import json
        return json.loads(data_str)

class XMLSerializationStrategy(SerializationStrategy):
    """Concrete strategy for XML serialization"""
    
    def serialize(self, data: Dict) -> str:
        from dicttoxml import dicttoxml
        return dicttoxml(data, custom_root='data', xml_declaration=False).decode()
    
    def deserialize(self, data_str: str) -> Dict:
        from xmltodict import parse
        return parse(data_str)

class SerializerManager:
    """Manages different serialization strategies and provides consistent interface"""
    
    def __init__(self, strategy: SerializationStrategy):
        self.strategy = strategy
        
    def serialize(self, data: Dict) -> str:
        """Delegate serialization to the current strategy"""
        return self.strategy.serialize(data)
    
    def deserialize(self, data_str: str) -> Dict:
        """Delegate deserialization to the current strategy"""
        return self.strategy.deserialize(data_str)

# Usage example
if __name__ == '__main__':
    data = {"name": "Alice", "age": 30}
    
    json_serializer = SerializerManager(JSONSerializationStrategy())
    json_data = json_serializer.serialize(data)
    print("JSON:", json_data)
    
    xml_serializer = SerializerManager(XMLSerializationStrategy())
    xml_data = xml_serializer.serialize(data)
    print("XML:", xml_data)