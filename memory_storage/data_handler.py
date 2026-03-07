from abc import ABC, abstractmethod
from typing import Dict, Any

class DataHandlerStrategy(ABC):
    """Abstract base class for data handling strategies"""
    
    @abstractmethod
    def serialize(self, data: Dict) -> str:
        """Serialize data to string format"""
        pass
    
    @abstractmethod
    def deserialize(self, data_str: str) -> Dict:
        """Deserialize string back to dictionary"""
        pass

class JSONDataHandler(DataHandlerStrategy):
    """JSON data handling strategy implementation"""
    
    def serialize(self, data: Dict) -> str:
        import json
        return json.dumps(data)
    
    def deserialize(self, data_str: str) -> Dict:
        import json
        return json.loads(data_str)

class XMLDataHandler(DataHandlerStrategy):
    """XML data handling strategy implementation"""
    
    def serialize(self, data: Dict) -> str:
        from dicttoxml import dicttoxml
        return dicttoxml(data, custom_root='data', xml_declaration=False).decode()
    
    def deserialize(self, data_str: str) -> Dict:
        from xmltodict import parse
        return parse(data_str)