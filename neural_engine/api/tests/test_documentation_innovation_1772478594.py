import pytest
from fastapi import FastAPI
from your_module import custom_openapi  # Replace with actual module name

def test_custom_openapi_happy_path():
    app = FastAPI()
    openapi_schema = custom_openapi(app)
    assert openapi_schema is not None
    assert "openapi" in openapi_schema
    assert "info" in openapi_schema
    assert "paths" in openapi_schema

def test_custom_openapi_no_app_routes():
    app = FastAPI(routes=[])
    openapi_schema = custom_openapi(app)
    assert openapi_schema is not None
    assert "openapi" in openapi_schema
    assert "info" in openapi_schema
    assert "paths" in openapi_schema

def test_custom_openapi_existing_openapi_schema():
    app = FastAPI()
    app.openapi_schema = {"openapi": "3.0.2"}
    openapi_schema = custom_openapi(app)
    assert openapi_schema == {"openapi": "3.0.2"}

# Uncomment and complete if you have an async behavior in the function
# @pytest.mark.asyncio
# async def test_custom_openapi_async_behavior():
#     app = FastAPI()
#     result = await custom_openapi(app)
#     assert result is not None