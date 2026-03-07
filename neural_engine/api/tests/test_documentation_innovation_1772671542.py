import pytest
from fastapi import FastAPI
from neural_engine.api.documentation import custom_openapi

def test_custom_openapi_happy_path():
    """Test normal operation with valid FastAPI app"""
    app = FastAPI()
    result = custom_openapi(app)
    
    assert result is not None
    assert "info" in result
    assert result["info"]["title"] == "Noug Neural OS API"
    assert result["info"]["version"] == "4.0.0"
    assert "x-logo" in result["info"]
    assert result["info"]["x-logo"]["url"] == "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"

def test_custom_openapi_with_existing_schema():
    """Test when app already has an openapi_schema"""
    app = FastAPI()
    expected_schema = {"dummy": "schema"}
    app.openapi_schema = expected_schema
    
    result = custom_openapi(app)
    assert result == expected_schema

def test_custom_openapi_with_invalid_app():
    """Test with invalid/None app parameter"""
    with pytest.raises(AttributeError):
        custom_openapi(None)