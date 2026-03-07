import pytest
from unittest.mock import MagicMock, patch
import os
import json

from unified_core.model_versioning import ModelVersioning

class TestModelVersioning:

    @pytest.fixture
    def model_versioning(self):
        return ModelVersioning(base_path="/path/to/base")

    @patch('os.path.exists')
    @patch('json.load')
    def test_load_model_happy_path(self, mock_json_load, mock_os_path_exists, model_versioning):
        # Arrange
        model_name = "test_model"
        version = 1
        base_path = "/path/to/base"
        version_path = os.path.join(base_path, f"{model_name}_v{version}")
        
        mock_os_path_exists.return_value = True
        
        model_data = {'key': 'value'}
        metadata = {'info': 'data'}
        
        with open(os.path.join(version_path, 'model.json'), 'w') as file:
            json.dump(model_data, file)
        
        with open(os.path.join(version_path, 'metadata.json'), 'w') as file:
            json.dump(metadata, file)
        
        # Act
        result = model_versioning.load_model(model_name, version)
        
        # Assert
        assert result == {'model': model_data, 'metadata': metadata}
        mock_os_path_exists.assert_called_once_with(version_path)
        mock_json_load.assert_has_calls([
            mock.call(open(os.path.join(version_path, 'model.json'), 'r')),
            mock.call(open(os.path.join(version_path, 'metadata.json'), 'r'))
        ])

    @patch('os.path.exists')
    def test_load_model_edge_case_empty_version(self, mock_os_path_exists, model_versioning):
        # Arrange
        model_name = "test_model"
        version = None
        base_path = "/path/to/base"
        
        mock_os_path_exists.return_value = False
        
        # Act & Assert
        with pytest.raises(FileNotFoundError) as exc_info:
            model_versioning.load_model(model_name, version)
        
        assert str(exc_info.value) == f"Model {model_name} version {version} not found."
        mock_os_path_exists.assert_called_once_with(os.path.join(base_path, f"{model_name}_vNone"))

    @patch('os.path.exists')
    def test_load_model_edge_case_empty_model_name(self, mock_os_path_exists, model_versioning):
        # Arrange
        model_name = None
        version = 1
        base_path = "/path/to/base"
        
        mock_os_path_exists.return_value = False
        
        # Act & Assert
        with pytest.raises(FileNotFoundError) as exc_info:
            model_versioning.load_model(model_name, version)
        
        assert str(exc_info.value) == f"Model {model_name} version {version} not found."
        mock_os_path_exists.assert_called_once_with(os.path.join(base_path, f"{None}_v1"))

    @patch('os.path.exists')
    def test_load_model_edge_case_empty_base_path(self, mock_os_path_exists, model_versioning):
        # Arrange
        model_name = "test_model"
        version = 1
        base_path = None
        
        mock_os_path_exists.return_value = False
        
        # Act & Assert
        with pytest.raises(FileNotFoundError) as exc_info:
            model_versioning.load_model(model_name, version)
        
        assert str(exc_info.value) == f"Model {model_name} version {version} not found."
        mock_os_path_exists.assert_called_once_with(os.path.join(None, f"{model_name}_v1"))

    @patch('os.path.exists')
    def test_load_model_edge_case_empty_inputs(self, mock_os_path_exists, model_versioning):
        # Arrange
        model_name = None
        version = None
        base_path = None
        
        mock_os_path_exists.return_value = False
        
        # Act & Assert
        with pytest.raises(FileNotFoundError) as exc_info:
            model_versioning.load_model(model_name, version)
        
        assert str(exc_info.value) == f"Model {model_name} version {version} not found."
        mock_os_path_exists.assert_called_once_with(os.path.join(None, f"{None}_v{None}"))