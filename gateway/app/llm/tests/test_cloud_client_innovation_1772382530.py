import pytest

class MockLLMCloudClient:
    def __init__(self):
        self.secrets = {
            "CLOUD_API_KEY": "test_api_key",
            "CLOUD_PROVIDER": "openai"
        }

    def generate(self, prompt: str, max_new_tokens: int = 500, timeout: float = None, **kwargs) -> str:
        """Call cloud API for inference (Synchronous)"""
        api_key = self.secrets.get("CLOUD_API_KEY")
        provider = self.secrets.get("CLOUD_PROVIDER", "").lower()

        if not api_key:
            return "[Error: Cloud API key not configured]"

        if provider in ["openai", "deepseek"]:
            return self._openai_generate(prompt, api_key, provider, max_new_tokens, timeout)
        else:
            return f"[Error: Unsupported provider '{provider}']"

    def _openai_generate(self, prompt: str, api_key: str, provider: str, max_new_tokens: int, timeout: float) -> str:
        if not prompt:
            return "[Error: Empty prompt]"
        return "Generated text based on prompt"

@pytest.fixture
def client():
    return MockLLMCloudClient()

def test_happy_path(client):
    result = client.generate("test prompt")
    assert result == "Generated text based on prompt"

def test_edge_case_empty_prompt(client):
    result = client.generate("")
    assert result == "[Error: Empty prompt]"

def test_edge_case_none_provider(client):
    client.secrets["CLOUD_PROVIDER"] = None
    result = client.generate("test prompt")
    assert result == "[Error: Cloud API key not configured]"

def test_error_case_unsupported_provider(client):
    client.secrets["CLOUD_PROVIDER"] = "unsupported"
    result = client.generate("test prompt")
    assert result == "[Error: Unsupported provider 'unsupported']"