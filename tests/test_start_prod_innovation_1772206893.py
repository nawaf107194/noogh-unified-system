import pytest
from unittest.mock import patch, MagicMock
import requests

def verify_health():
    logger.info("--- 3. HEALTH CHECKS ---")
    
    # Check Gateway Liveness
    try:
        resp = requests.get("http://localhost:8000/health", timeout=2)
        if resp.status_code == 200:
            logger.info("✅ Gateway Alive")
        else:
            logger.error(f"❌ Gateway Health Failed: {resp.status_code}")
    except Exception as e:
        logger.error(f"❌ Gateway Unreachable: {e}")
        
    # Check Gateway Readiness (Dependencies)
    try:
        resp = requests.get("http://localhost:8000/ready", timeout=2)
        if resp.status_code == 200:
            logger.info("✅ System Ready (Redis+Neural+Sandbox)")
        else:
            logger.error(f"❌ System Not Ready: {resp.json()}")
    except Exception:
        pass

# Mock the logger to capture output
@pytest.fixture
def logger():
    with patch('start_prod.logger', autospec=True) as mock_logger:
        yield mock_logger

@patch('requests.get')
def test_verify_health_gateway_liveness_success(mock_get, logger):
    mock_get.return_value.status_code = 200
    verify_health()
    assert logger.info.call_args_list == [
        pytest.call("--- 3. HEALTH CHECKS ---"),
        pytest.call("✅ Gateway Alive")
    ]

@patch('requests.get')
def test_verify_health_gateway_liveness_failure(mock_get, logger):
    mock_get.side_effect = requests.RequestException("Gateway Error")
    verify_health()
    assert logger.error.call_args_list == [
        pytest.call("--- 3. HEALTH CHECKS ---"),
        pytest.call("❌ Gateway Unreachable: Gateway Error")
    ]

@patch('requests.get')
def test_verify_health_gateway_readiness_success(mock_get, logger):
    mock_get.return_value.status_code = 200
    verify_health()
    assert logger.info.call_args_list == [
        pytest.call("--- 3. HEALTH CHECKS ---"),
        pytest.call("✅ Gateway Alive"),
        pytest.call("✅ System Ready (Redis+Neural+Sandbox)")
    ]

@patch('requests.get')
def test_verify_health_gateway_readiness_failure(mock_get, logger):
    mock_get.side_effect = requests.RequestException("Readiness Error")
    verify_health()
    assert logger.error.call_args_list == [
        pytest.call("--- 3. HEALTH CHECKS ---"),
        pytest.call("✅ Gateway Alive"),
        pytest.call("❌ System Not Ready: None")
    ]