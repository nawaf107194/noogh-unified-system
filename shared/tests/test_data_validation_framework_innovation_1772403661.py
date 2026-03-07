import pytest
from jsonschema import validate, ValidationError
from noogh_unified_system.src.shared.data_validation_framework import DataValidationFramework

class MockSchema:
    def __init__(self):
        self.schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 0}
            },
            "required": ["name"]
        }

def test_validate_data_happy_path():
    dvf = DataValidationFramework(MockSchema())
    data = {"name": "John Doe", "age": 30}
    result = dvf.validate_data(data)
    assert result is None

def test_validate_data_empty_input():
    dvf = DataValidationFramework(MockSchema())
    data = {}
    result = dvf.validate_data(data)
    assert result is None

def test_validate_data_none_input():
    dvf = DataValidationFramework(MockSchema())
    data = None
    result = dvf.validate_data(data)
    assert result is None

def test_validate_data_boundary_value():
    dvf = DataValidationFramework(MockSchema())
    data = {"name": "John Doe", "age": 0}
    result = dvf.validate_data(data)
    assert result is None

def test_validate_data_invalid_schema():
    dvf = DataValidationFramework(MockSchema())
    data = {"name": "John Doe", "age": -1}
    with pytest.raises(ValidationError):
        dvf.validate_data(data)

def test_validate_data_missing_required_field():
    dvf = DataValidationFramework(MockSchema())
    data = {"age": 30}
    with pytest.raises(ValidationError):
        dvf.validate_data(data)