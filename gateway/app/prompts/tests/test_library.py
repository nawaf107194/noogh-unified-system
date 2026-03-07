import pytest
from unittest.mock import patch, MagicMock
from gateway.app.prompts.library import LibraryClass  # Assuming the class containing _load_metadata is named LibraryClass
import logging

# Mock the logger to avoid actual log outputs during testing
logger = logging.getLogger(__name__)
logger.warning = MagicMock()
logger.error = MagicMock()

@pytest.fixture
def library_instance(tmp_path):
    metadata_file = tmp_path / "metadata.json"
    instance = LibraryClass(metadata_file=metadata_file)
    instance.metadata = {}
    return instance

class TestLoadMetadata:

    @pytest.mark.parametrize("data", [
        {"prompt1": {"key": "value"}},
        {"prompt1": {}, "prompt2": {"key": "value"}},
        {},
    ])
    def test_happy_path(self, library_instance, tmp_path, data):
        metadata_file = library_instance.metadata_file
        metadata_file.write_text(json.dumps(data))
        library_instance._load_metadata()
        assert library_instance.metadata == {k: PromptMetadata(**v) for k, v in data.items()}

    def test_file_does_not_exist(self, library_instance):
        library_instance._load_metadata()
        logger.warning.assert_called_once_with("Metadata file does not exist.")

    @patch('builtins.open', side_effect=Exception("Mocked file read error"))
    def test_file_read_error(self, mock_open, library_instance):
        library_instance._load_metadata()
        logger.error.assert_called_once_with("Failed to load metadata from file: Mocked file read error")

    def test_invalid_json_format(self, library_instance, tmp_path):
        metadata_file = library_instance.metadata_file
        metadata_file.write_text("invalid json")
        library_instance._load_metadata()
        logger.error.assert_called_once_with("Failed to load metadata from file: Expecting value: line 1 column 1 (char 0)")

    def test_invalid_metadata_reconstruction(self, library_instance, tmp_path):
        metadata_file = library_instance.metadata_file
        metadata_file.write_text('{"prompt1": {"invalid_key": "value"}}')
        library_instance._load_metadata()
        logger.error.assert_called_once_with(f"Failed to reconstruct metadata for prompt1: __init__() got an unexpected keyword argument 'invalid_key'")

    def test_empty_metadata_file(self, library_instance, tmp_path):
        metadata_file = library_instance.metadata_file
        metadata_file.write_text("{}")
        library_instance._load_metadata()
        assert library_instance.metadata == {}

    def test_none_metadata_file(self, library_instance):
        library_instance.metadata_file = None
        library_instance._load_metadata()
        logger.warning.assert_called_once_with("Metadata file does not exist.")