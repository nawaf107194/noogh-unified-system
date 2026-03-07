import pytest
from typing import Dict, Any
from unittest.mock import Mock

class TestConfigManager:
    def setup_method(self):
        self.config_manager = Mock()
        self.config_manager.config_data = {}

    def test_validate_config_success(self):
        # Test normal case with valid config
        self.config_manager.config_data = {
            "section1": {
                "key1": "value1",
                "key2": 123
            },
            "section2": {
                "key3": True
            }
        }
        required_sections = {
            "section1": {
                "key1": str,
                "key2": int
            },
            "section2": {
                "key3": bool
            }
        }
        
        # Should not raise any exceptions
        self.config_manager.validate_config(required_sections)
        
    def test_validate_config_missing_section(self):
        # Test missing section
        self.config_manager.config_data = {
            "section1": {
                "key1": "value1"
            }
        }
        required_sections = {
            "section2": {
                "key2": int
            }
        }
        
        with pytest.raises(ValueError, match="Section 'section2' is missing"):
            self.config_manager.validate_config(required_sections)
            
    def test_validate_config_missing_key(self):
        # Test missing key in section
        self.config_manager.config_data = {
            "section1": {
                "key1": "value1"
            }
        }
        required_sections = {
            "section1": {
                "key1": str,
                "key2": int
            }
        }
        
        with pytest.raises(ValueError, match="Key 'key2' is missing"):
            self.config_manager.validate_config(required_sections)
            
    def test_validate_config_type_mismatch(self):
        # Test type mismatch
        self.config_manager.config_data = {
            "section1": {
                "key1": 123  # Wrong type
            }
        }
        required_sections = {
            "section1": {
                "key1": str
            }
        }
        
        with pytest.raises(TypeError, match="Type mismatch for key 'key1'"):
            self.config_manager.validate_config(required_sections)
            
    def test_validate_config_empty_required_sections(self):
        # Test with empty required sections
        self.config_manager.config_data = {}
        required_sections = {}
        
        # Should not raise any exceptions
        self.config_manager.validate_config(required_sections)
        
    def test_validate_config_none_value(self):
        # Test with None value
        self.config_manager.config_data = {
            "section1": {
                "key1": None
            }
        }
        required_sections = {
            "section1": {
                "key1": type(None)
            }
        }
        
        # Should not raise any exceptions
        self.config_manager.validate_config(required_sections)