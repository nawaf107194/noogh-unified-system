import pytest
from gateway.app.plugins.signing import sign_bytes
import hmac
import hashlib

def test_sign_bytes_happy_path():
    data = b"test_data"
    key = "my_secret_key"
    signature = sign_bytes(data, key)
    assert isinstance(signature, str)

def test_sign_bytes_empty_data():
    data = b""
    key = "my_secret_key"
    signature = sign_bytes(data, key)
    assert isinstance(signature, str)

def test_sign_bytes_none_data():
    data = None
    key = "my_secret_key"
    with pytest.raises(ValueError):
        sign_bytes(data, key)

def test_sign_bytes_empty_key():
    data = b"test_data"
    key = ""
    with pytest.raises(ValueError):
        sign_bytes(data, key)