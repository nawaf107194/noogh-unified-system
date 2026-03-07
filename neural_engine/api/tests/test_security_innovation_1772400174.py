from fastapi import HTTPException, Header
from unittest.mock import patch

def _get_internal_token():
    return "expected_token"

@pytest.fixture(autouse=True)
def mock_get_internal_token():
    with patch('neural_engine.api.security._get_internal_token', return_value="expected_token"):
        yield

def test_verify_internal_token_happy_path(mocker):
    # Setup
    mocker.spy(verify_internal_token, 'logger')

    # Call
    result = verify_internal_token("expected_token")

    # Assert
    assert result is True
    verify_internal_token.logger.info.assert_called_once_with('✅ [verify_internal_token] Valid token received: expected_token')

def test_verify_internal_token_empty_token():
    with pytest.raises(HTTPException) as exc_info:
        verify_internal_token("")
    
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "No internal token provided in request headers"

def test_verify_internal_token_none_token():
    with pytest.raises(HTTPException) as exc_info:
        verify_internal_token(None)
    
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "No internal token provided in request headers"

def test_verify_internal_token_invalid_type():
    with pytest.raises(HTTPException) as exc_info:
        verify_internal_token(123)
    
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid type for internal token, expected string"

def test_verify_internal_token_no_expected_token(mocker):
    with patch('neural_engine.api.security._get_internal_token', return_value=None):
        with pytest.raises(HTTPException) as exc_info:
            verify_internal_token("expected_token")
        
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Server misconfigured: NOOGH_INTERNAL_TOKEN not set"