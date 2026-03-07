import pytest

from config.ports import get_service_url, NEURAL_PORT, GATEWAY_PORT

def test_get_service_url_happy_path():
    assert get_service_url("neural") == f"http://127.0.0.1:{NEURAL_PORT}"
    assert get_service_url("gateway") == f"http://127.0.0.1:{GATEWAY_PORT}"

def test_get_service_url_edge_cases():
    assert get_service_url("") is None  # Assuming empty string should return None
    assert get_service_url(None) is None  # Assuming None should return None

def test_get_service_url_error_cases():
    with pytest.raises(KeyError):
        assert get_service_url("unknown_service") == "http://localhost"  # Assuming unknown service raises KeyError