import pytest

from gateway.app.core.skills import get_skills_instance, AgentSkills

def test_get_skills_instance_happy_path():
    """Test with normal inputs."""
    data_dir = "test_data"
    result = get_skills_instance(data_dir)
    assert isinstance(result, AgentSkills)
    assert result.safe_root == data_dir

def test_get_skills_instance_with_default_directory():
    """Test with empty data_dir to use default directory."""
    data_dir = ""
    result = get_skills_instance(data_dir)
    assert isinstance(result, AgentSkills)
    assert result.safe_root == "."

def test_get_skills_instance_none_data_dir():
    """Test with None data_dir to use default directory."""
    result = get_skills_instance(None)
    assert isinstance(result, AgentSkills)
    assert result.safe_root == "."

def test_get_skills_instance_invalid_input():
    """Test with invalid input type."""
    invalid_input = 123
    result = get_skills_instance(invalid_input)
    assert result is None

def test_get_skills_instance_explicit_none_return():
    """Test explicit None return in case of error."""
    def mock_get_skills_instance(data_dir: str) -> AgentSkills:
        raise ValueError("Invalid data directory")
    
    with pytest.raises(ValueError):
        get_skills_instance("invalid_data_dir")