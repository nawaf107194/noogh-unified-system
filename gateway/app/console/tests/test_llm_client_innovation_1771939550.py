import os
from unittest.mock import patch, mock_open

from gateway.app.console.llm_client import LLMClient

class TestLLMClient:

    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.client = LLMClient()

    def test_happy_path(self):
        # Mock the prompt file exists and contains content
        with patch('builtins.open', mock_open(read_data="You are UC3, the Unified Cognitive Agent.")):
            assert self.client.system_prompt == "You are UC3, the Unified Cognitive Agent."

    def test_edge_case_empty_file(self):
        # Mock the prompt file exists but is empty
        with patch('builtins.open', mock_open(read_data="")):
            assert self.client.system_prompt == ""

    def test_edge_case_no_file_exists(self):
        with patch.object(os.path, 'exists', return_value=False):
            assert self.client.system_prompt == "You are UC3, the Unified Cognitive Agent."

    def test_error_case_invalid_path(self):
        # Mock an invalid path
        prompt_path = os.path.join(os.path.dirname(__file__), "nonexistent_path.txt")
        with patch.object(os.path, 'exists', return_value=False):
            assert self.client.system_prompt == "You are UC3, the Unified Cognitive Agent."

    def test_error_case_file_read_failure(self):
        # Mock a failure to read the file
        with patch('builtins.open', side_effect=IOError("Failed to open file")):
            assert self.client.system_prompt == "You are UC3, the Unified Cognitive Agent."