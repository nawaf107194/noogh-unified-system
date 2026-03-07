import pytest

class MockApp:  # A minimal mock for an app object
    pass

def test_init_happy_path():
    middleware = Middleware(MockApp(), max_bytes=1024 * 512)  # 512KB
    assert isinstance(middleware, Middleware)
    assert middleware.max_bytes == 1024 * 512

def test_init_edge_case_max_bytes_zero():
    middleware = Middleware(MockApp(), max_bytes=0)
    assert isinstance(middleware, Middleware)
    assert middleware.max_bytes == 0

def test_init_edge_case_max_bytes_negative():
    middleware = Middleware(MockApp(), max_bytes=-1024 * 512)
    assert isinstance(middleware, Middleware)
    assert middleware.max_bytes == -1024 * 512

def test_init_edge_case_max_bytes_none():
    middleware = Middleware(MockApp(), max_bytes=None)
    assert isinstance(middleware, Middleware)
    assert middleware.max_bytes is None

def test_init_error_case_invalid_input_type():
    with pytest.raises(TypeError):
        Middleware("not a Flask app object", max_bytes=1024 * 512)

# Note: Since the function does not use any async behavior (it's synchronous),
# there is no need to test for async behavior in this case.