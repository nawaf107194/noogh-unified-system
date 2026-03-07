import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from pathlib import Path

import neural_engine.tools.security_tools as security_tools

BLOCKED_IPS_FILE = Path("/path/to/blocked_ips.json")

def mock_ensure_security_dirs():
    pass  # Mocking this function to avoid side effects

@patch('neural_engine.tools.security_tools._ensure_security_dirs', mock_ensure_security_dirs)
@patch('neural_engine.tools.security_tools.BLOCKED_IPS_FILE', new_callable=MagicMock)
def test_unblock_ip_happy_path(mock_file):
    ip = "192.168.1.1"
    mock_file.read_text.return_value = json.dumps([{"ip": ip, "reason": "test"}])
    
    result = security_tools.unblock_ip(ip)
    
    assert result == {"success": True, "ip": ip, "unblocked": True}
    mock_file.write_text.assert_called_once_with(
        json.dumps([{"ip": ip, "reason": "test"}], indent=2)
    )
    subprocess.run.assert_called_once_with(
        ["sudo", "iptables", "-D", "INPUT", "-s", ip, "-j", "DROP"],
        capture_output=True,
        timeout=5
    )
    security_tools.log_security_event.assert_called_once_with({
        "action": "unblock_ip",
        "ip": ip,
        "timestamp": datetime.now().isoformat()
    })

@patch('neural_engine.tools.security_tools._ensure_security_dirs', mock_ensure_security_dirs)
def test_unblock_ip_ip_not_blocked(mock_file):
    ip = "192.168.1.1"
    mock_file.read_text.return_value = json.dumps([{"ip": "192.168.1.2", "reason": "test"}])
    
    result = security_tools.unblock_ip(ip)
    
    assert result == {"success": False, "error": f"IP {ip} was not blocked"}
    mock_file.write_text.assert_not_called()
    subprocess.run.assert_not_called()
    security_tools.log_security_event.assert_not_called()

@patch('neural_engine.tools.security_tools._ensure_security_dirs', mock_ensure_security_dirs)
def test_unblock_ip_empty_list(mock_file):
    ip = "192.168.1.1"
    mock_file.read_text.return_value = json.dumps([])
    
    result = security_tools.unblock_ip(ip)
    
    assert result == {"success": False, "error": f"IP {ip} was not blocked"}
    mock_file.write_text.assert_not_called()
    subprocess.run.assert_not_called()
    security_tools.log_security_event.assert_not_called()

@patch('neural_engine.tools.security_tools._ensure_security_dirs', mock_ensure_security_dirs)
def test_unblock_ip_none_input(mock_file):
    result = security_tools.unblock_ip(None)
    
    assert result == {"success": False, "error": "'NoneType' object is not iterable"}
    mock_file.write_text.assert_not_called()
    subprocess.run.assert_not_called()
    security_tools.log_security_event.assert_not_called()

@patch('neural_engine.tools.security_tools._ensure_security_dirs', mock_ensure_security_dirs)
def test_unblock_ip_invalid_input(mock_file):
    result = security_tools.unblock_ip("invalid ip")
    
    assert result == {"success": False, "error": "'NoneType' object is not iterable"}
    mock_file.write_text.assert_not_called()
    subprocess.run.assert_not_called()
    security_tools.log_security_event.assert_not_called()