import json
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from gateway.app.core.ast_validator import validate_python
from gateway.app.core.persistent_memory import _atomic_write_json
from gateway.app.main import app


class TestHardeningPatches:
    """Test suite for security hardening patches (v0.4.1)"""

    # --- Patch #1: AST Validation ---

    def test_ast_blocks_forbidden_names(self):
        """AST validator blocks eval, exec, open, etc."""
        dangerous_codes = [
            "eval('print(1)')",
            "exec('import os')",
            "f = open('test.txt', 'w')",
            "__import__('os').system('ls')",
        ]
        for code in dangerous_codes:
            result = validate_python(code)
            assert result.ok is False
            assert any(reason.startswith("Forbidden name") or "Import" in reason for reason in result.reasons)

    def test_ast_blocks_introspection(self):
        """AST validator blocks introspection tricks"""
        code = "[].__class__.__mro__[1].__subclasses__()"
        result = validate_python(code)
        assert result.ok is False
        assert any("Forbidden attribute access" in reason for reason in result.reasons)

    def test_ast_blocks_infinite_loops(self):
        """AST validator blocks while True"""
        code = "while True: pass"
        result = validate_python(code)
        assert result.ok is False
        assert any("infinite loop" in reason.lower() for reason in result.reasons)

    # --- Patch #2: Bearer Token Auth ---

    def test_api_requires_auth(self):
        # pytest.skip("TestClient is not compatible with current monkeypatches and Python 3.12 anyio portal.")

        client = TestClient(app)

        # Invalid token should not break health (still 200)
        response = client.get("/health", headers={"Authorization": "Bearer wrong-token"})
        assert response.status_code == 200

        # Valid token
        response = client.get("/health", headers={"Authorization": "Bearer test-admin-token"})
        assert response.status_code == 200

        # Protected endpoint: /task requires a valid token
        task_payload = {"task": "Hello"}
        # No token -> unauthorized
        response = client.post("/task", json=task_payload)
        assert response.status_code == 401

        # Invalid token -> unauthorized
        response = client.post("/task", json=task_payload, headers={"Authorization": "Bearer wrong-token"})
        assert response.status_code == 401

        # Valid token -> kernel not initialized returns 503 in this test context
        response = client.post("/task", json=task_payload, headers={"Authorization": "Bearer test-admin-token"})
        assert response.status_code in (200, 503)

    # --- Patch #3: Atomic Storage ---

    def test_atomic_write_integrity(self):
        """Atomic write ensures file integrity and proper JSON format"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.json"
            data = {"key": "value", "nested": [1, 2, 3]}

            _atomic_write_json(str(test_file), data)

            assert test_file.exists()
            with open(test_file, "r") as f:
                loaded = json.load(f)
                assert loaded == data

            # Check if lock file was created (side effect)
            assert Path(str(test_file) + ".lock").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
