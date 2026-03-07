import pytest

from gateway.app.api.dashboard import validate_window_seconds, HTTPException


def test_validate_window_seconds_happy_path():
    # Happy path: normal inputs
    assert validate_window_seconds(1) == 1
    assert validate_window_seconds(86400) == 86400


def test_validate_window_seconds_edge_cases():
    # Edge cases: boundaries
    with pytest.raises(HTTPException, match="window must be positive"):
        validate_window_seconds(-1)
    
    with pytest.raises(HTTPException, match="window cannot exceed 86400 seconds"):
        validate_window_seconds(86401)


def test_validate_window_seconds_error_cases():
    # Error cases: invalid inputs
    with pytest.raises(HTTPException, match="window must be positive"):
        validate_window_seconds(0)
    
    with pytest.raises(HTTPException, match="window cannot exceed 86400 seconds"):
        validate_window_seconds(86401)