import pytest
from shared.data_serializer import serialize

def test_serialize_json_happy_path():
    data = {'key': 'value'}
    result = serialize(data, format='json')
    assert result == '{"key": "value"}'

def test_serialize_yaml_happy_path():
    data = {'key': 'value'}
    result = serialize(data, format='yaml')
    assert result == "key: value\n"

def test_serialize_json_empty_input():
    data = {}
    result = serialize(data, format='json')
    assert result == '{}'

def test_serialize_yaml_empty_input():
    data = {}
    result = serialize(data, format='yaml')
    assert result == ""

def test_serialize_json_none_input():
    data = None
    result = serialize(data, format='json')
    assert result is None

def test_serialize_yaml_none_input():
    data = None
    result = serialize(data, format='yaml')
    assert result is None

def test_serialize_invalid_format():
    data = {'key': 'value'}
    with pytest.raises(ValueError):
        serialize(data, format='xml')