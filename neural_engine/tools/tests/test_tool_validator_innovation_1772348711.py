import pytest

from neural_engine.tools.tool_validator import validate_url, ValidationError

def test_validate_url_happy_path():
    valid_urls = [
        "http://example.com",
        "https://www.example.org",
        "http://1.2.3.4",
        "https://[2001:db8::1]"
    ]
    
    for url in valid_urls:
        result = validate_url(url)
        assert result == url, f"Expected {url} to be validated as {url}, got {result}"

def test_validate_url_empty_input():
    with pytest.raises(ValidationError) as excinfo:
        validate_url("")
    assert "Invalid URL: No scheme supplied" in str(excinfo.value)

def test_validate_url_none_input():
    with pytest.raises(ValidationError) as excinfo:
        validate_url(None)
    assert "Invalid URL: No scheme supplied" in str(excinfo.value)

def test_validate_url_no_scheme():
    with pytest.raises(ValidationError) as excinfo:
        validate_url("example.com")
    assert "Invalid URL: No scheme supplied" in str(excinfo.value)

def test_validate_url_unsupported_scheme():
    with pytest.raises(ValidationError) as excinfo:
        validate_url("ftp://example.com")
    assert "Unsafe URL scheme: ftp" in str(excinfo.value)

def test_validate_url_missing_hostname():
    with pytest.raises(ValidationError) as excinfo:
        validate_url("http://")
    assert "URL missing hostname" in str(excinfo.value)

def test_validate_url_internal_ip():
    blocked_patterns = [
        '127.',      # localhost
        '10.',       # Private class A
        '172.16.',   # Private class B start
        '192.168.',  # Private class C
        'localhost',
        '0.0.0.0',
        '[::]',      # IPv6 localhost
    ]
    
    for pattern in blocked_patterns:
        url = f"http://{pattern}example.com"
        with pytest.raises(ValidationError) as excinfo:
            validate_url(url)
        assert f"URL points to internal network: {pattern}" in str(excinfo.value)

def test_validate_url_invalid_url_format():
    with pytest.raises(ValidationError) as excinfo:
        validate_url("://example.com")
    assert "Invalid URL: No scheme supplied" in str(excinfo.value)