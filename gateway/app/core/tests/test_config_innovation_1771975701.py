import pytest

from gateway.app.core.config import get_settings, Settings

@pytest.fixture
def settings_instance():
    return Settings()

def test_get_settings_happy_path(settings_instance):
    """Test that get_settings returns a valid Settings instance."""
    result = get_settings()
    assert isinstance(result, Settings)

def test_get_settings_edge_case_none():
    """Test that get_settings handles None input gracefully."""
    with pytest.raises(TypeError):
        get_settings(None)

def test_get_settings_edge_case_empty():
    """Test that get_settings handles empty input gracefully."""
    with pytest.raises(TypeError):
        get_settings("")

def test_get_settings_error_case_invalid_input():
    """Test that get_settings handles invalid input gracefully."""
    with pytest.raises(TypeError):
        get_settings(123)