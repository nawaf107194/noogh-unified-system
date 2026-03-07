import pytest
from unittest.mock import Mock
from typing import Optional
from gateway.app.security.cloudflare_access import get_user_email

class Request:
    def __init__(self, headers: dict):
        self.headers = headers

@pytest.fixture
def mock_request():
    return Request({})

def test_get_user_email_happy_path(mock_request):
    mock_request.headers["CF-Access-Authenticated-User-Email"] = "test@example.com"
    assert get_user_email(mock_request) == "test@example.com"

def test_get_user_email_empty_header(mock_request):
    assert get_user_email(mock_request) is None

def test_get_user_email_none_request():
    with pytest.raises(AttributeError):
        get_user_email(None)

def test_get_user_email_invalid_header_type():
    invalid_request = Mock(headers=123)
    with pytest.raises(AttributeError):
        get_user_email(invalid_request)

def test_get_user_email_missing_header(mock_request):
    assert get_user_email(mock_request) is None

def test_get_user_email_with_other_headers(mock_request):
    mock_request.headers.update({"CF-Access-Other-Header": "other_value"})
    assert get_user_email(mock_request) is None

def test_get_user_email_with_special_characters(mock_request):
    mock_request.headers["CF-Access-Authenticated-User-Email"] = "test+special@characters.com"
    assert get_user_email(mock_request) == "test+special@characters.com"

def test_get_user_email_async_behavior():
    # Since the function does not involve any asynchronous operations,
    # we don't need to write an async test.
    pass