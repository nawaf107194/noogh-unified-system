import pytest
from src.shared.data_serializer import serialize
import json
import yaml

def test_serialize_json_with_complex_data():
    """Test JSON serialization with complex nested data"""
    data = {
        "name": "test",
        "nested": {
            "list": [1, 2, 3],
            "bool": True,
            "null": None
        }
    }
    result = serialize(data, format='json')
    assert isinstance(result, str)
    assert result != ""
    assert json.loads(result) == data

def test_serialize_yaml_with_complex_data():
    """Test YAML serialization with complex nested data"""
    data = {
        "name": "test",
        "nested": {
            "list": [1, 2, 3],
            "bool": True,
            "null": None
        }
    }
    result = serialize(data, format='yaml')
    assert isinstance(result, str)
    assert result != ""
    assert yaml.safe_load(result) == data

def test_serialize_with_empty_data():
    """Test serialization with empty data"""
    data = {}
    result_json = serialize(data, format='json')
    result_yaml = serialize(data, format='yaml')
    assert json.loads(result_json) == {}
    assert yaml.safe_load(result_yaml) == {}

def test_serialize_with_none():
    """Test serialization with None value"""
    data = None
    result_json = serialize(data, format='json')
    result_yaml = serialize(data, format='yaml')
    assert result_json == "null"
    assert result_yaml.strip() == "null"

def test_invalid_format():
    """Test serialization with invalid format"""
    with pytest.raises(ValueError, match="Unsupported format. Use 'json' or 'yaml'."):
        serialize({}, format='xml')