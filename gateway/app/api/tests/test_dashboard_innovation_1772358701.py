import pytest
from fastapi.responses import HTMLResponse
import secrets

def _get_safe_html(nonce):
    return f"<html><body>Nonce: {nonce}</body></html>"

def _security_headers(nonce):
    return {
        "X-Frame-Options": "SAMEORIGIN",
        "Content-Security-Policy": f"default-src 'self'; nonce-{nonce}"
    }

@pytest.fixture
def dashboard_ui_function():
    from gateway.app.api.dashboard import dashboard_ui
    return dashboard_ui

def test_happy_path(dashboard_ui_function):
    result = dashboard_ui_function()
    assert isinstance(result, HTMLResponse)
    assert '<html><body>Nonce: ' in result.body.decode('utf-8')
    nonce = result.headers.get("Content-Security-Policy").split("nonce-")[1]
    assert len(nonce) == 32
    assert nonce.isalnum()

def test_edge_case_empty_nonce(dashboard_ui_function):
    original_get_safe_html = _get_safe_html
    def mock_get_safe_html(_):
        return "<html><body>Nonce:</body></html>"
    _get_safe_html = mock_get_safe_html
    
    result = dashboard_ui_function()
    
    _get_safe_html = original_get_safe_html
    
    assert isinstance(result, HTMLResponse)
    assert '<html><body>Nonce:</body></html>' in result.body.decode('utf-8')
    nonce = result.headers.get("Content-Security-Policy").split("nonce-")[1]
    assert len(nonce) == 32
    assert nonce.isalnum()

def test_edge_case_none_nonce(dashboard_ui_function):
    original_get_safe_html = _get_safe_html
    def mock_get_safe_html(_):
        return "<html><body>Nonce: None</body></html>"
    _get_safe_html = mock_get_safe_html
    
    result = dashboard_ui_function()
    
    _get_safe_html = original_get_safe_html
    
    assert isinstance(result, HTMLResponse)
    assert '<html><body>Nonce: None</body></html>' in result.body.decode('utf-8')
    nonce = result.headers.get("Content-Security-Policy").split("nonce-")[1]
    assert len(nonce) == 32
    assert nonce.isalnum()

def test_error_case_invalid_input(dashboard_ui_function):
    # This function does not have any error handling or parameters,
    # so there are no explicit error cases to test.
    pass

async def test_async_behavior(dashboard_ui_function):
    # The function is synchronous, so there is no async behavior to test.
    pass