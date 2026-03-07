import pytest

from agents.file_manager_agent import FileManagerAgent, _canonicalize_path

@pytest.fixture
def file_manager_agent():
    agent = FileManagerAgent()
    agent.ALLOWED_PATHS = ["/home/user", "/mnt/external"]
    return agent

def test_is_path_allowed_happy_path(file_manager_agent):
    # Normal inputs
    assert file_manager_agent._is_path_allowed("/home/user/documents/file.txt") == True
    assert file_manager_agent._is_path_allowed("/mnt/external/data.csv") == True

def test_is_path_allowed_edge_cases(file_manager_agent):
    # Empty string
    assert file_manager_agent._is_path_allowed("") == False
    
    # None
    assert file_manager_agent._is_path_allowed(None) == False
    
    # Boundary cases (exact allowed paths)
    assert file_manager_agent._is_path_allowed("/home/user") == True
    assert file_manager_agent._is_path_allowed("/mnt/external") == True

def test_is_path_allowed_error_cases(file_manager_agent):
    # Invalid inputs (non-string)
    with pytest.raises(TypeError):
        file_manager_agent._is_path_allowed(123)
    
    # Path outside allowed directories
    assert file_manager_agent._is_path_allowed("/etc/passwd") == False
    assert file_manager_agent._is_path_allowed("/home/otheruser/documents/file.txt") == False

def test_is_path_allowed_async_behavior_file_manager_agent(file_manager_agent, monkeypatch):
    async def mock_canonicalize_path(path):
        return path
    
    monkeypatch.setattr(FileManagerAgent, "_canonicalize_path", mock_canonicalize_path)
    
    # Test with async behavior
    assert file_manager_agent._is_path_allowed("/home/user/documents/file.txt") == True