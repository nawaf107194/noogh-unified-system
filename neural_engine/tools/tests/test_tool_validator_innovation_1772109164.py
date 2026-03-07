import pytest

def test_validate_url_happy_path():
    assert validate_url("http://example.com") == "http://example.com"
    assert validate_url("https://www.example.org") == "https://www.example.org"

def test_validate_url_edge_cases():
    assert validate_url("") is None
    assert validate_url(None) is None

def test_validate_url_error_cases():
    with pytest.raises(ValidationError) as exc_info:
        validate_url("ftp://example.com")
    assert str(exc_info.value) == "Invalid URL: unknown url type 'ftp'"

    with pytest.raises(ValidationError) as exc_info:
        validate_url("http://127.0.0.1")
    assert str(exc_info.value) == "URL points to internal network: 127.0.0.1 (SSRF prevention)"

    with pytest.raises(ValidationError) as exc_info:
        validate_url("http://localhost")
    assert str(exc_info.value) == "URL points to internal network: localhost (SSRF prevention)"

    with pytest.raises(ValidationError) as exc_info:
        validate_url("https://[::]")
    assert str(exc_info.value) == "URL points to internal network: [::] (SSRF prevention)"