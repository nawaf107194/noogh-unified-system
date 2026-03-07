import pytest

class MockApp:
    pass

def test_init_happy_path():
    middleware = Middleware(MockApp(), max_bytes=512 * 1024)
    assert middleware.max_bytes == 512 * 1024

def test_init_default_value():
    middleware = Middleware(MockApp())
    assert middleware.max_bytes == 1024 * 1024

def test_init_with_zero_bytes():
    middleware = Middleware(MockApp(), max_bytes=0)
    assert middleware.max_bytes == 0

def test_init_with_none_app():
    with pytest.raises(TypeError):
        Middleware(None, max_bytes=1024 * 1024)

def test_init_with_negative_max_bytes():
    with pytest.raises(ValueError):
        Middleware(MockApp(), max_bytes=-1024 * 1024)

def test_init_with_non_integer_max_bytes():
    with pytest.raises(TypeError):
        Middleware(MockApp(), max_bytes="not an integer")

def test_init_with_float_max_bytes():
    middleware = Middleware(MockApp(), max_bytes=1024 * 1024.5)
    assert middleware.max_bytes == int(1024 * 1024.5)

# Assuming there's no async behavior in the provided __init__ method.
# If there was, we would need to mock or patch the async calls and use pytest-asyncio.
# For now, we skip async behavior testing as it's not applicable based on the given function.