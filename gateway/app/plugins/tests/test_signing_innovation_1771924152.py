import pytest
from gateway.app.plugins.signing import sign_bytes
import hmac
import hashlib

def test_sign_bytes_happy_path():
    data = b"Hello, world!"
    key = "secret_key"
    expected_signature = hmac.new(key.encode(), data, hashlib.sha256).hexdigest()
    assert sign_bytes(data, key) == expected_signature

def test_sign_bytes_empty_data():
    data = b""
    key = "secret_key"
    expected_signature = hmac.new(key.encode(), data, hashlib.sha256).hexdigest()
    assert sign_bytes(data, key) == expected_signature

def test_sign_bytes_none_data():
    with pytest.raises(ValueError):
        sign_bytes(None, "secret_key")

def test_sign_bytes_empty_key():
    data = b"Hello, world!"
    key = ""
    with pytest.raises(ValueError):
        sign_bytes(data, key)

def test_sign_bytes_none_key():
    data = b"Hello, world!"
    with pytest.raises(ValueError):
        sign_bytes(data, None)