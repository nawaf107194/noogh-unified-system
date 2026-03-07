import pytest
from unittest.mock import patch, Mock
from noogh_unified_system.src.agents.server_control_agent import ServerControlAgent

@pytest.fixture
def agent():
    return ServerControlAgent()

@patch('subprocess.run')
def test_restart_service_happy_path(mock_run, agent):
    mock_run.return_value = Mock(returncode=0)
    
    result = agent.restart_service("example_service")
    
    assert result == True
    mock_run.assert_called_once_with(
        ["sudo", "systemctl", "restart", "example_service"],
        capture_output=True, text=True, timeout=30
    )
    logger.info.assert_called_once_with(f"  ✅ Restarted: example_service")

@patch('subprocess.run')
def test_restart_service_empty_input(mock_run, agent):
    mock_run.return_value = Mock(returncode=0)
    
    result = agent.restart_service("")
    
    assert result == False
    mock_run.assert_not_called()
    logger.warning.assert_called_once_with(f"  ❌ Restart failed: | ")

@patch('subprocess.run')
def test_restart_service_none_input(mock_run, agent):
    mock_run.return_value = Mock(returncode=0)
    
    result = agent.restart_service(None)
    
    assert result == False
    mock_run.assert_not_called()
    logger.warning.assert_called_once_with(f"  ❌ Restart failed: | ")

@patch('subprocess.run')
def test_restart_service_invalid_input(mock_run, agent):
    mock_run.return_value = Mock(returncode=1)
    
    result = agent.restart_service("invalid_service")
    
    assert result == False
    mock_run.assert_called_once_with(
        ["sudo", "systemctl", "restart", "invalid_service"],
        capture_output=True, text=True, timeout=30
    )
    logger.warning.assert_called_once_with(f"  ❌ Restart failed: invalid_service | ")