import pytest
from typing import Dict, Any

def test_emergency_lockdown_happy_path():
    result = emergency_lockdown("Malware detected")
    assert result["success"] is True
    assert result["lockdown"] is True
    assert result["reason"] == "Malware detected"
    assert "Security event logged" in result["actions_taken"]
    assert "Alert triggered" in result["actions_taken"]
    assert "Ready for manual intervention" in result["actions_taken"]
    assert result["note"] == "Full lockdown requires manual confirmation"

def test_emergency_lockdown_empty_reason():
    result = emergency_lockdown("")
    assert result["success"] is True
    assert result["lockdown"] is True
    assert result["reason"] == ""
    assert "Security event logged" in result["actions_taken"]
    assert "Alert triggered" in result["actions_taken"]
    assert "Ready for manual intervention" in result["actions_taken"]
    assert result["note"] == "Full lockdown requires manual confirmation"

def test_emergency_lockdown_none_reason():
    result = emergency_lockdown(None)
    assert result["success"] is True
    assert result["lockdown"] is True
    assert result["reason"] is None
    assert "Security event logged" in result["actions_taken"]
    assert "Alert triggered" in result["actions_taken"]
    assert "Ready for manual intervention" in result["actions_taken"]
    assert result["note"] == "Full lockdown requires manual confirmation"

def test_emergency_lockdown_invalid_input():
    with pytest.raises(TypeError):
        emergency_lockdown(123)

def test_emergency_lockdown_no_severity_logging():
    # Assuming log_security_event is a mock or a function that logs to a file
    result = emergency_lockdown("Unauthorized access")
    assert result["success"] is True
    assert result["lockdown"] is True
    assert result["reason"] == "Unauthorized access"
    assert "Security event logged" in result["actions_taken"]
    assert "Alert triggered" in result["actions_taken"]
    assert "Ready for manual intervention" in result["actions_taken"]
    assert result["note"] == "Full lockdown requires manual confirmation"

# Assuming logger is a module-level variable that can be mocked
from unittest.mock import patch, MagicMock

@patch('neural_engine.tools.security_tools.logger.critical')
def test_emergency_lockdown_logger(mock_critical):
    emergency_lockdown("Phishing attempt")
    mock_critical.assert_called_once_with("🚨 EMERGENCY LOCKDOWN: Phishing attempt")