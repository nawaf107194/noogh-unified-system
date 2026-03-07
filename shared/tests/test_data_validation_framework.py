import pytest
import json
from shared.data_validation_framework import DataValidationFramework

def test_happy_path():
    schema_path = "path/to/valid_schema.json"
    with open(schema_path, 'w') as file:
        json.dump({}, file)
    
    dvf = DataValidationFramework(schema_path)
    assert dvf.schema == {}

def test_edge_case_empty_schema():
    schema_path = "path/to/empty_schema.json"
    with open(schema_path, 'w') as file:
        json.dump({}, file)
    
    dvf = DataValidationFramework(schema_path)
    assert dvf.schema == {}

def test_edge_case_none_schema_path():
    with pytest.raises(FileNotFoundError):
        dvf = DataValidationFramework(None)

def test_error_case_invalid_schema_path():
    with pytest.raises(FileNotFoundError):
        dvf = DataValidationFramework("path/to/nonexistent_file.json")