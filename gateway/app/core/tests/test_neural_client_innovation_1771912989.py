import pytest
from typing import Dict

from gateway.app.core.neural_client import NeuralClient, get_neural_client

class TestNeuralClient:

    @pytest.fixture
    def valid_secrets(self) -> Dict[str, str]:
        return {
            'api_key': 'test_api_key',
            'api_secret': 'test_api_secret'
        }

    def test_happy_path(self, valid_secrets):
        """Test normal inputs."""
        client = get_neural_client(valid_secrets)
        assert isinstance(client, NeuralClient)

    def test_edge_case_empty_secrets(self):
        """Test empty secrets dictionary."""
        client = get_neural_client({})
        assert client is None

    def test_edge_case_none_secrets(self):
        """Test None as secrets."""
        client = get_neural_client(None)
        assert client is None

    def test_error_case_invalid_input_type(self, valid_secrets):
        """Test invalid input type (e.g., list instead of dict)."""
        client = get_neural_client(['invalid', 'input'])
        assert client is None