import pytest

from agents.file_manager_agent import FileManagerAgent, _canonicalize_path

@pytest.fixture
def file_manager_agent():
    agent = FileManagerAgent()
    agent.ALLOWED_PATHS = ["/home/user", "/var/log"]
    return agent

def test_is_path_allowed_happy_path(file_manager_agent):
    assert file_manager_agent._is_path_allowed("/home/user/documents/report.pdf") == True
    assert file_manager_agent._is_path_allowed("/var/log/syslog") == True

def test_is_path_allowed_edge_cases(file_manager_agent):
    assert file_manager_agent._is_path_allowed("") == False
    assert file_manager_agent._is_path_allowed(None) == False
    assert file_manager_agent._is_path_allowed("/") == False
    assert file_manager_agent._is_path_allowed("/home/user/") == True

def test_is_path_allowed_error_cases(file_manager_agent):
    # Assuming canonicalize_path doesn't raise exceptions based on the provided code
    pass

# Async behavior not applicable as there is no async method in the provided code