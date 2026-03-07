import pytest

from gateway.app.security.cloudflare_access import is_mfa_verified, Request

class MockRequest:
    def __init__(self, headers=None):
        self.headers = headers or {}
        self.client = MockClient()

class MockClient:
    def __init__(self, host="127.0.0.1"):
        self.host = host

def test_is_mfa_verified_happy_path():
    request = Request(headers={
        "CF-Access-JWT-Assertion": "example_jwt",
        "CF-Access-Authenticated-User-Email": "user@example.com"
    })
    assert is_mfa_verified(request) == True

def test_is_mfa_verified_empty_headers():
    request = Request(headers={})
    assert is_mfa_verified(request) == False

def test_is_mfa_verified_missing_jwt():
    request = Request(headers={
        "CF-Access-Authenticated-User-Email": "user@example.com"
    })
    assert is_mfa_verified(request) == False

def test_is_mfa_verified_missing_email():
    request = Request(headers={
        "CF-Access-JWT-Assertion": "example_jwt"
    })
    assert is_mfa_verified(request) == False

def test_is_mfa_verified_localhost_bypass():
    request = MockRequest(headers={
        "CF-Access-JWT-Assertion": "example_jwt",
        "CF-Access-Authenticated-User-Email": "user@example.com"
    }, client=MockClient(host="127.0.0.1"))
    assert is_mfa_verified(request) == True

def test_is_mfa_verified_dev_bypass():
    request = MockRequest(headers={
        "CF-Access-JWT-Assertion": "example_jwt",
        "CF-Access-Authenticated-User-Email": "user@example.com"
    }, client=MockClient(host="localhost"))
    assert is_mfa_verified(request) == True

def test_is_mfa_verified_boundary_conditions():
    request = MockRequest(headers={
        "CF-Access-JWT-Assertion": "example_jwt",
        "CF-Access-Authenticated-User-Email": "user@example.com"
    }, client=MockClient(host="::1"))
    assert is_mfa_verified(request) == True