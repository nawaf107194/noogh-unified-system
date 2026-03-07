
from fastapi.testclient import TestClient

from gateway.app.main import app

client = TestClient(app)


def test_health(monkeypatch):
    import asyncio
    from unittest.mock import Mock

    from gateway.app.api.routes import health_check

    monkeypatch.setenv("NOOGH_ADMIN_TOKEN", "test-admin-token")
    mock_request = Mock()
    result = asyncio.run(health_check(mock_request))
    assert result["status"] in ["ok", "starting"]
