import pytest
from neural_engine.tools.tool_validator import validate_url, ValidationError

def test_validate_url_happy_path():
    valid_urls = [
        "http://example.com",
        "https://www.example.org",
        "http://127.0.0.1/path?query=string",
    ]
    for url in valid_urls:
        assert validate_url(url) == url

def test_validate_url_empty_input():
    with pytest.raises(ValidationError):
        validate_url("")

def test_validate_url_none_input():
    with pytest.raises(ValidationError):
        validate_url(None)

def test_validate_url_missing_scheme():
    with pytest.raises(ValidationError):
        validate_url("example.com")

def test_validate_url_unsupported_scheme():
    with pytest.raises(ValidationError):
        validate_url("ftp://example.com")

def test_validate_url_internal_ip():
    internal_ips = [
        "http://127.0.0.1",
        "https://10.0.0.1",
        "http://172.16.0.1",
        "https://192.168.0.1",
        "http://localhost",
        "https://[::]",
        "http://0.0.0.0",
    ]
    for url in internal_ips:
        with pytest.raises(ValidationError):
            validate_url(url)

def test_validate_url_valid_internal_ip():
    valid_internals = [
        "http://192.168.1.1",
        "https://172.17.0.2",
        "http://10.10.10.10",
        "https://[2001:db8::1]",
    ]
    for url in valid_internals:
        assert validate_url(url) == url

# If the function is async, you would need to use pytest-asyncio and define these tests as async