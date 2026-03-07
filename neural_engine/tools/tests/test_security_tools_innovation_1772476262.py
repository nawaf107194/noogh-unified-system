import pytest
from unittest.mock import mock_open, patch
from datetime import datetime
from neural_engine.tools.security_tools import block_ip

# Mock open function for JSON file operations
MOCKED_IPS_FILE = json.dumps([
    {"ip": "192.168.1.1", "reason": "Test", "blocked_at": datetime.now().isoformat()}
])

@patch("neural_engine.tools.security_tools._ensure_security_dirs")
@patch("neural_engine.tools.security_tools.log_security_event")
@patch("builtins.open", new_callable=mock_open, read_data=MOCKED_IPS_FILE)
def test_block_ip_happy_path(mocked_open, mock_log_security_event, mock_ensure_dirs):
    result = block_ip("192.168.1.2", "Normal activity")
    assert result == {
        "success": True,
        "ip": "192.168.1.2",
        "blocked": True,
        "method": "iptables",
        "reason": "Normal activity"
    }
    mock_log_security_event.assert_called_once()
    mocked_open.assert_has_calls([
        (mocked_open.return_value.write, json.dumps([{
            "ip": "192.168.1.2", 
            "reason": "Normal activity",
            "blocked_at": datetime.now().isoformat()
        }, {"ip": "192.168.1.1", "reason": "Test", "blocked_at": datetime.now().isoformat()}], indent=2))
    ])
    
@patch("neural_engine.tools.security_tools._ensure_security_dirs")
@patch("neural_engine.tools.security_tools.log_security_event")
def test_block_ip_empty_string(mock_log_security_event, mock_ensure_dirs):
    result = block_ip("")
    assert result == {
        "success": False,
        "error": "Invalid IP format: "
    }
    mock_log_security_event.assert_not_called()
    
@patch("neural_engine.tools.security_tools._ensure_security_dirs")
@patch("neural_engine.tools.security_tools.log_security_event")
def test_block_ip_none(mock_log_security_event, mock_ensure_dirs):
    result = block_ip(None)
    assert result == {
        "success": False,
        "error": "Invalid IP format: None"
    }
    mock_log_security_event.assert_not_called()
    
@patch("neural_engine.tools.security_tools._ensure_security_dirs")
@patch("neural_engine.tools.security_tools.log_security_event")
def test_block_ip_invalid_format(mock_log_security_event, mock_ensure_dirs):
    result = block_ip("192.168.1")
    assert result == {
        "success": False,
        "error": "Invalid IP format: 192.168.1"
    }
    mock_log_security_event.assert_not_called()
    
@patch("neural_engine.tools.security_tools._ensure_security_dirs")
@patch("neural_engine.tools.security_tools.log_security_event")
def test_block_ip_already_blocked(mock_log_security_event, mock_ensure_dirs):
    result = block_ip("192.168.1.1", "Duplicate entry")
    assert result == {
        "success": True,
        "ip": "192.168.1.1",
        "blocked": False,
        "method": "software",
        "reason": "Duplicate entry"
    }
    mock_log_security_event.assert_called_once()
    
@patch("neural_engine.tools.security_tools._ensure_security_dirs")
@patch("neural_engine.tools.security_tools.log_security_event")
@patch("subprocess.run", side_effect=Exception("Iptables error"))
def test_block_ip_iptables_error(mock_run, mock_log_security_event, mock_ensure_dirs):
    result = block_ip("192.168.1.3")
    assert result == {
        "success": True,
        "ip": "192.168.1.3",
        "blocked": True,
        "method": "software",
        "reason": "Suspicious activity",
        "note": "Blocked in NOOGH only, not at OS firewall level"
    }
    mock_log_security_event.assert_called_once()