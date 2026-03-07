import pytest
from src.agents.backup_agent_agent import BackupAgentAgent

def test_backup_agent_agent_init():
    # Happy path: Initialize with default parameters
    backup_agent = BackupAgentAgent()
    
    # Verify custom handlers are initialized
    assert hasattr(backup_agent, 'custom_handlers')
    assert len(backup_agent.custom_handlers) == 2
    assert "CREATE_BACKUP" in backup_agent.custom_handlers
    assert "VERIFY_BACKUP" in backup_agent.custom_handlers
    
    # Verify agent role is set
    assert backup_agent.role.name == "backup_agent"
    
    # Edge case: Verify initialization with no arguments
    backup_agent_empty = BackupAgentAgent()
    assert backup_agent_empty is not None
    
    # Error case: Verify initialization does not raise exceptions
    # since no explicit exceptions are raised in __init__