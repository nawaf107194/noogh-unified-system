import pytest
from .signing import sign_bytes
import hmac
import hashlib

# Mock data for testing
test_data = b"test_data"
test_key = "test_key"

# Expected result for the happy path
expected_signature = hmac.new(test_key.encode(), test_data, hashlib.sha256).hexdigest()

def test_sign_bytes_happy_path():
    assert sign_bytes(test_data, test_key) == expected_signature

def test_sign_bytes_empty_data():
    assert sign_bytes(b"", test_key) == hmac.new(test_key.encode(), b"", hashlib.sha256).hexdigest()

def test_sign_bytes_none_data():
    with pytest.raises(TypeError):
        sign_bytes(None, test_key)

def test_sign_bytes_empty_key():
    with pytest.raises(ValueError):
        sign_bytes(test_data, "")

def test_sign_bytes_none_key():
    with pytest.raises(ValueError):
        sign_bytes(test_data, None)

def test_sign_bytes_invalid_key_type():
    with pytest.raises(AttributeError):
        sign_bytes(test_data, 12345)

def test_sign_bytes_invalid_data_type():
    with pytest.raises(AttributeError):
        sign_bytes("test_string", test_key)

# Since the function does not involve any asynchronous operations,
# there's no need to test for async behavior.