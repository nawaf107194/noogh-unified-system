import pytest
from fastapi import FastAPI, Request
from starlette.types import ASGIApp

class MockMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope, receive, send):
        pass

@pytest.fixture
def middleware():
    return MockMiddleware

@pytest.mark.asyncio
async def test_init_happy_path(middleware):
    app = FastAPI()
    instance = middleware(app)
    assert instance.max_bytes == 10_000_000
    assert instance.app is app

@pytest.mark.asyncio
async def test_init_edge_case_max_bytes_none(middleware):
    app = FastAPI()
    instance = middleware(app, max_bytes=None)
    assert instance.max_bytes == 10_000_000
    assert instance.app is app

@pytest.mark.asyncio
async def test_init_edge_case_max_bytes_empty_string(middleware):
    app = FastAPI()
    instance = middleware(app, max_bytes="")
    assert instance.max_bytes == 10_000_000
    assert instance.app is app

@pytest.mark.asyncio
async def test_init_error_case_non_integer_max_bytes(middleware):
    app = FastAPI()
    with pytest.raises(TypeError) as exc_info:
        middleware(app, max_bytes="invalid")
    assert str(exc_info.value) == "max_bytes must be an integer"

@pytest.mark.asyncio
async def test_init_edge_case_max_bytes_zero(middleware):
    app = FastAPI()
    instance = middleware(app, max_bytes=0)
    assert instance.max_bytes == 10_000_000
    assert instance.app is app

# No need for async behavior tests since the __init__ method does not perform any async operations