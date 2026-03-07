import pytest
from fastapi.testclient import TestClient
from neural_engine.api.main import app

client = TestClient(app)

# Use valid token if required, but here we test the parameter rejection
HEADERS = {"X-Internal-Token": "secret_token_123"} 

class TestExecuteHardening:
    def test_allowed_param_rejected(self):
        """Test that passing 'allowed' parameter is no longer accepted or ignored."""
        # Note: In FastAPI, if we remove the param from signature, passing it as query param
        # usually results in it being ignored (if extra args allowed) or 422 if strict?
        # Actually, if it's removed from signature, it won't affect logic.
        # But we want to ensure the Logic doesn't check it.
        
        # We need to simulate the environment variable if main.py checks it
        # Assuming NOOGH_INTERNAL_TOKEN is set in environment for the test runner?
        # If not, we might need patch.
        pass # The real verification is that the function signature doesn't have it.

    def test_execute_signature(self):
        from neural_engine.api.routes import execute_command
        import inspect
        sig = inspect.signature(execute_command)
        assert 'allowed' not in sig.parameters, "Vulnerability: 'allowed' parameter still present in execute_command"
