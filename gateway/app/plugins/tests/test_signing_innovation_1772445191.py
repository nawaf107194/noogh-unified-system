import pytest
from gateway.app.plugins.signing import verify_signature, sign_bytes

def test_happy_path():
    data = b'example_data'
    key = 'secret_key'
    signature = sign_bytes(data, key)
    assert verify_signature(data, signature, key) is True

def test_empty_signature():
    data = b'example_data'
    key = 'secret_key'
    signature = ''
    assert verify_signature(data, signature, key) is False

def test_empty_key():
    data = b'example_data'
    key = ''
    signature = sign_bytes(data, 'other_secret')
    assert verify_signature(data, signature, key) is False

def test_none_signature():
    data = b'example_data'
    key = 'secret_key'
    signature = None
    assert verify_signature(data, signature, key) is False

def test_none_key():
    data = b'example_data'
    key = None
    signature = sign_bytes('other_secret', key)
    assert verify_signature(data, signature, key) is False

def test_boundary_signature_length():
    data = b'example_data'
    key = 'secret_key'
    signature = 'a' * 64  # Minimum length for SHA256
    assert verify_signature(data, signature, key) is True

def test_boundary_signature_length_too_short():
    data = b'example_data'
    key = 'secret_key'
    signature = 'a' * 63  # Too short for SHA256
    assert verify_signature(data, signature, key) is False

def test_boundary_signature_length_too_long():
    data = b'example_data'
    key = 'secret_key'
    signature = 'a' * 66  # Too long for SHA256
    assert verify_signature(data, signature, key) is False