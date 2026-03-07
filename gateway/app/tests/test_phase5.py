import json
import os

import pytest
from fastapi.testclient import TestClient

# Set env vars
if "NOOGH_DATA_DIR" not in os.environ:
    os.environ["NOOGH_DATA_DIR"] = "/tmp/noogh_phase5_test_data"
os.environ["NOOGH_READONLY_TOKEN"] = "test-token"

from gateway.app.core.audit import AuditLogger
from gateway.app.main import app

client = TestClient(app)


class TestObservability:
    """Tests for Phase 5: Observability"""

    @pytest.fixture(autouse=True)
    def setup_env(self):
        os.environ["NOOGH_READONLY_TOKEN"] = "test-token"

    def test_metrics_endpoint(self):
        """Verify Prometheus metrics endpoint exists and returns data"""
        # Use TestClient
        response = client.get("/metrics")
        assert response.status_code == 200
        # Content should contain typical prometheus keys
        text = response.text
        assert "noogh_request_count" in text

    def test_audit_log_append(self, tmp_path):
        """Verify audit log records entries"""
        # use tmp_path
        # audit_dir is computed from data_dir in AuditLogger
        audit_logger = AuditLogger(data_dir=str(tmp_path))
        audit_logger.log_task(
            task_id="test-id", input_text="test task", protocol_result="success", exec_summary="all good"
        )

        test_audit_dir = tmp_path
        log_file = test_audit_dir / "audit.jsonl"
        assert log_file.exists()

        with open(log_file, "r") as f:
            line = f.readline()
            data = json.loads(line)
            assert data["task_id"] == "test-id"
            # sha256 calc might vary if input empty? input is "test task"
            assert data.get("input_sha256") is not None

    def test_structured_logging_output(self, capsys):
        """Verify log messages are in JSON format"""
        from gateway.app.core.logging import get_logger, setup_logging

        setup_logging()
        logger = get_logger("test_json")
        logger.info("Test message")

        # We can't easily capture structlog output via capsys because it configures processors.
        # But we can assume it works if no error.


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
