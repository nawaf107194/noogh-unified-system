import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from pathlib import Path
from neural_engine.tools.security_tools import block_ip, _ensure_security_dirs

# Mocks and fixtures
BLOCKED_IPS_FILE = MagicMock(spec=Path)
BLOCKED_IPS_CONTENT = '[{"ip": "1.2.3.4", "reason": "Test", "blocked_at": "2023-04-01T00:00:00"}]'
BLOCKED_IPS_FILE.read_text.return_value = BLOCKED_IPS_CONTENT
BLOCKED_IPS_FILE.write_text.side_effect = None

logger = MagicMock()

@pytest.fixture(autouse=True)
def setup_security_dirs():
    with patch('neural_engine.tools.security_tools._ensure_security_dirs') as mock:
        yield mock

@pytest.fixture(autouse=True)
def setup_logger():
    with patch('neural_engine.tools.security_tools.logger', new=MagicMock()) as mock:
        yield mock

@pytest.fixture(autouse=True)
def setup_block_ips_file():
    global BLOCKED_IPS_FILE
    BLOCKED_IPS_FILE = MagicMock(spec=Path)
    BLOCKED_IPS_FILE.read_text.return_value = BLOCKED_IPS_CONTENT
    BLOCKED_IPS_FILE.write_text.side_effect = None
    with patch('neural_engine.tools.security_tools.BLOCKED_IPS_FILE', new=BLOCKED_IPS_FILE):
        yield

# Tests
def test_block_ip_happy_path():
    result = block_ip("8.8.8.8", "Malicious activity")
    assert result == {
        "success": True,
        "ip": "8.8.8.8",
        "blocked": True,
        "method": "iptables",
        "reason": "Malicious activity"
    }
    BLOCKED_IPS_FILE.write_text.assert_called_once()
    logger.info.assert_called_once()

def test_block_ip_invalid_ip():
    result = block_ip("999.256.100.10", "Invalid IP")
    assert result == {
        "success": False,
        "error": "Invalid IP format: 999.256.100.10"
    }
    logger.error.assert_not_called()
    BLOCKED_IPS_FILE.write_text.assert_not_called()

def test_block_ip_empty_reason():
    result = block_ip("8.8.8.8", "")
    assert result == {
        "success": True,
        "ip": "8.8.8.8",
        "blocked": True,
        "method": "software",
        "reason": "",
        "note": "Blocked in NOOGH only, not at OS firewall level"
    }
    BLOCKED_IPS_FILE.write_text.assert_called_once()
    logger.warning.assert_called_once()

def test_block_ip_no_iptables_access():
    with patch('subprocess.run') as mock:
        mock.side_effect = Exception("Failed to execute iptables command")
        result = block_ip("8.8.8.8", "No iptables access")
    assert result == {
        "success": True,
        "ip": "8.8.8.8",
        "blocked": True,
        "method": "software",
        "reason": "No iptables access",
        "note": "Blocked in NOOGH only, not at OS firewall level"
    }
    BLOCKED_IPS_FILE.write_text.assert_called_once()
    logger.warning.assert_called_once()

def test_block_ip_iptables_success():
    with patch('subprocess.run') as mock:
        mock.return_value = MagicMock(returncode=0)
        result = block_ip("8.8.8.8", "Iptables success")
    assert result == {
        "success": True,
        "ip": "8.8.8.8",
        "blocked": True,
        "method": "iptables",
        "reason": "Iptables success"
    }
    BLOCKED_IPS_FILE.write_text.assert_called_once()
    logger.info.assert_called_once()