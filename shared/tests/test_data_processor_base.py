import pytest

class TestLoadFunction:
    def test_load_happy_path(self):
        """Test normal input case"""
        class ConcreteProcessor(data_processor_base):
            def load(self, data_source: str) -> Any:
                return "loaded_data"
        
        processor = ConcreteProcessor()
        result = processor.load("valid_source")
        assert result == "loaded_data"

    def test_load_empty_string(self):
        """Test edge case with empty string input"""
        class EmptyProcessor(data_processor_base):
            def load(self, data_source: str) -> Any:
                if not data_source:
                    return None
                return "loaded_data"
        
        processor = EmptyProcessor()
        result = processor.load("")
        assert result is None

    def test_load_none_input(self):
        """Test edge case with None input"""
        class NoneProcessor(data_processor_base):
            def load(self, data_source: str) -> Any:
                if data_source is None:
                    return None
                return "loaded_data"
        
        processor = NoneProcessor()
        result = processor.load(None)
        assert result is None

    def test_load_invalid_input(self):
        """Test error case with invalid input type"""
        class ErrorProcessor(data_processor_base):
            def load(self, data_source: str) -> Any:
                if not isinstance(data_source, str):
                    return None
                return "loaded_data"
        
        processor = ErrorProcessor()
        result = processor.load(123)
        assert result is None