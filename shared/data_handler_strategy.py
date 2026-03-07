from abc import ABC, abstractmethod

class DataHandlerStrategy(ABC):
    """Abstract base class for data handling strategies"""
    
    @abstractmethod
    def serialize(self, data):
        """Serialize data to target format"""
        pass
    
    @abstractmethod
    def deserialize(self, data):
        """Deserialize data from source format"""
        pass
    
    @abstractmethod
    def transform(self, data):
        """Transform data according to defined rules"""
        pass
    
    @abstractmethod
    def validate(self, data):
        """Validate data integrity"""
        pass

class CSVStrategy(DataHandlerStrategy):
    """Concrete strategy for CSV data handling"""
    
    def serialize(self, data):
        # Implement CSV serialization logic
        pass
    
    def deserialize(self, data):
        # Implement CSV deserialization logic
        pass
    
    def transform(self, data):
        # Implement CSV transformation logic
        pass
    
    def validate(self, data):
        # Implement CSV validation logic
        pass

class JSONStrategy(DataHandlerStrategy):
    """Concrete strategy for JSON data handling"""
    
    def serialize(self, data):
        # Implement JSON serialization logic
        pass
    
    def deserialize(self, data):
        # Implement JSON deserialization logic
        pass
    
    def transform(self, data):
        # Implement JSON transformation logic
        pass
    
    def validate(self, data):
        # Implement JSON validation logic
        pass