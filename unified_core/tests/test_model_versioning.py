import pytest
from unittest.mock import patch, MagicMock
from typing import List
import os

# Assuming the class is defined as part of a larger class structure
class MockModelVersioning:
    def __init__(self, base_path):
        self.base_path = base_path

    def list_versions(self, model_name: str) -> List[int]:
        """List all available versions for a given model."""
        versions = []
        for item in os.listdir(self.base_path):
            if item.startswith(f"{model_name}_v"):
                try:
                    version = int(item.split('_v')[1])
                    versions.append(version)
                except ValueError:
                    continue
        return sorted(versions)

@pytest.fixture
def mock_model_versioning():
    with patch('os.listdir', return_value=['model_v1', 'model_v2', 'model_v3', 'model_v10']):
        return MockModelVersioning('/mock/path')

def test_list_versions_happy_path(mock_model_versioning):
    assert mock_model_versioning.list_versions('model') == [1, 2, 3, 10]

def test_list_versions_empty_directory(mock_model_versioning):
    with patch('os.listdir', return_value=[]):
        assert mock_model_versioning.list_versions('model') == []

def test_list_versions_none_model_name(mock_model_versioning):
    with patch('os.listdir', return_value=['model_v1', 'model_v2', 'model_v3']):
        assert mock_model_versioning.list_versions(None) == []

def test_list_versions_invalid_model_name(mock_model_versioning):
    with patch('os.listdir', return_value=['invalid_model_v1', 'model_v2']):
        assert mock_model_versioning.list_versions('model') == [2]

def test_list_versions_with_non_integer_versions(mock_model_versioning):
    with patch('os.listdir', return_value=['model_v1', 'model_v2', 'model_vnonint']):
        assert mock_model_versioning.list_versions('model') == [1, 2]

def test_list_versions_with_mixed_versions(mock_model_versioning):
    with patch('os.listdir', return_value=['model_v1', 'model_v2', 'model_v3', 'model_v1.5']):
        assert mock_model_versioning.list_versions('model') == [1, 2, 3]

def test_list_versions_with_no_valid_versions(mock_model_versioning):
    with patch('os.listdir', return_value=['model_vnonint', 'model_vnonint2']):
        assert mock_model_versioning.list_versions('model') == []

def test_list_versions_with_unicode_characters(mock_model_versioning):
    with patch('os.listdir', return_value=['model_v1', 'model_v2', 'model_v\u00e9']):
        assert mock_model_versioning.list_versions('model') == [1, 2]