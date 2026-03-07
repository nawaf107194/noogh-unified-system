import pytest
from unittest.mock import Mock
from typing import Optional

# Assuming the Request class is part of some framework like FastAPI or similar
class Request:
    def __init__(self, headers: dict = None):
        self.headers = headers if headers else {}

def get_user_email(request: Request) -> Optional[str]:
    return request.headers.get("CF-Access-Authenticated-User-Email")

# Test cases
def test_get_user_email_happy_path():
    headers = {"CF-Access-Authenticated-User-Email": "test@example.com"}
    request = Request(headers=headers)
    assert get_user_email(request) == "test@example.com"

def test_get_user_email_empty_headers():
    request = Request()
    assert get_user_email(request) is None

def test_get_user_email_none_request():
    with pytest.raises(AttributeError):
        get_user_email(None)

def test_get_user_email_invalid_header_key():
    headers = {"Invalid-Key": "test@example.com"}
    request = Request(headers=headers)
    assert get_user_email(request) is None

def test_get_user_email_invalid_header_value():
    headers = {"CF-Access-Authenticated-User-Email": ""}
    request = Request(headers=headers)
    assert get_user_email(request) == ""

# Since the function does not involve async operations, there's no need to test async behavior.