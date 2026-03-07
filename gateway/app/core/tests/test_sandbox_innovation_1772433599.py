import pytest
from unittest.mock import patch, MagicMock
from gateway.app.core.sandbox import Sandbox

def test_execute_code_happy_path():
    sandbox = Sandbox(service_url="http://mock-service")
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"output": "Hello, World!"}
        mock_post.return_value = mock_response

        result = sandbox.execute_code(code="print('Hello, World!')")

    assert result == {"success": True, "output": "Hello, World!", "error": "", "exit_code": 0, "duration_ms": pytest.approx(0)}

def test_execute_code_empty_code():
    sandbox = Sandbox(service_url="http://mock-service")
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"output": ""}
        mock_post.return_value = mock_response

        result = sandbox.execute_code(code="")

    assert result == {"success": False, "output": "", "error": "Sandbox Service Error (200)", "exit_code": -1, "duration_ms": pytest.approx(0)}

def test_execute_code_none_code():
    sandbox = Sandbox(service_url="http://mock-service")
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"output": ""}
        mock_post.return_value = mock_response

        result = sandbox.execute_code(code=None)

    assert result == {"success": False, "output": "", "error": "Sandbox Service Error (200)", "exit_code": -1, "duration_ms": pytest.approx(0)}

def test_execute_code_invalid_language():
    sandbox = Sandbox(service_url="http://mock-service")
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Unsupported language"}
        mock_post.return_value = mock_response

        result = sandbox.execute_code(code="print('Hello, World!')", language="invalid")

    assert result == {"success": False, "output": "", "error": "Sandbox Service Error (400)", "exit_code": -1, "duration_ms": pytest.approx(0)}

def test_execute_code_request_timeout():
    sandbox = Sandbox(service_url="http://mock-service")
    with patch("requests.post") as mock_post:
        mock_post.side_effect = requests.exceptions.Timeout

        result = sandbox.execute_code(code="print('Hello, World!')")

    assert result == {"success": False, "output": "", "error": "Sandbox Request Timed Out (> 10s)", "exit_code": -1, "duration_ms": pytest.approx(0)}

def test_execute_code_connection_error():
    sandbox = Sandbox(service_url="http://mock-service")
    with patch("requests.post") as mock_post:
        mock_post.side_effect = requests.exceptions.RequestException

        result = sandbox.execute_code(code="print('Hello, World!')")

    assert result == {"success": False, "output": "", "error": "Connection Error: [Errno -2] Name or service not known", "exit_code": -1, "duration_ms": pytest.approx(0)}