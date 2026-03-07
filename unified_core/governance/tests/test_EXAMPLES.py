import pytest
from unified_core.governance import flags
from EXAMPLES import rollback_if_needed

def test_rollback_if_needed_happy_path():
    # Reset flags to known state
    flags.GOVERNANCE_ENABLED = True
    flags.WRAP_PROCESS_SPAWN = True
    flags.DRY_RUN = False
    
    # Call function
    rollback_if_needed()
    
    # Verify flags were set correctly
    assert flags.GOVERNANCE_ENABLED is False
    assert flags.WRAP_PROCESS_SPAWN is False
    assert flags.DRY_RUN is True
    
    # Verify output contains correct status
    captured = pytest.capsys.readouterr()
    assert "Governance status" in captured.out
    assert "GOVERNANCE_ENABLED: False" in captured.out
    assert "WRAP_PROCESS_SPAWN: False" in captured.out
    assert "DRY_RUN: True" in captured.out

def test_rollback_if_needed_edge_cases():
    # Test with flags already disabled
    flags.GOVERNANCE_ENABLED = False
    flags.WRAP_PROCESS_SPAWN = False
    flags.DRY_RUN = True
    
    # Call function again
    rollback_if_needed()
    
    # Verify flags remain disabled
    assert flags.GOVERNANCE_ENABLED is False
    assert flags.WRAP_PROCESS_SPAWN is False
    assert flags.DRY_RUN is True
    
    # Verify output still contains status
    captured = pytest.capsys.readouterr()
    assert "Governance status" in captured.out

def test_rollback_if_needed_multiple_calls():
    # First call
    rollback_if_needed()
    
    # Second call
    rollback_if_needed()
    
    # Verify flags remain in rolled-back state
    assert flags.GOVERNANCE_ENABLED is False
    assert flags.WRAP_PROCESS_SPAWN is False
    assert flags.DRY_RUN is True