import pytest
from unittest.mock import patch, mock_open

# Assuming the LLMClient class is defined in the same file
from gateway.app.console.llm_client import LLMClient

class TestLLMClientInit:

    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data="Mocked System Prompt")
    def test_happy_path(self, mock_file, mock_exists):
        llm_client = LLMClient()
        assert llm_client.system_prompt == "Mocked System Prompt"

    @patch('os.path.exists', return_value=False)
    def test_file_not_found(self, mock_exists):
        llm_client = LLMClient()
        assert llm_client.system_prompt == "You are UC3, the Unified Cognitive Agent."

    @patch('os.path.exists', side_effect=[True, False])
    @patch('builtins.open', side_effect=FileNotFoundError())
    def test_file_read_error(self, mock_file, mock_exists):
        with pytest.raises(FileNotFoundError):
            LLMClient()

    @patch('os.path.exists', side_effect=[False, True])
    def test_fallback_message(self, mock_exists):
        llm_client = LLMClient()
        assert llm_client.system_prompt == "You are UC3, the Unified Cognitive Agent."