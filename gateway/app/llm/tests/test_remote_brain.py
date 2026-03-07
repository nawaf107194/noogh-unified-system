import pytest
from unittest.mock import patch, MagicMock
from config.ports import PORTS
from gateway.app.llm.remote_brain import RemoteBrainService

@pytest.fixture
def mock_os_env():
    with patch('os.getenv', return_value=None) as mock_env:
        yield mock_env

@pytest.fixture
def mock_logger_info():
    with patch('gateway.app.llm.remote_brain.logger.info') as mock_logger:
        yield mock_logger

@pytest.fixture
def mock_settings_base_model_name():
    with patch('gateway.app.llm.remote_brain.settings.BASE_MODEL_NAME', 'gpt-3.5-turbo'):
        yield

@pytest.mark.usefixtures('mock_os_env', 'mock_logger_info', 'mock_settings_base_model_name')
def test_remote_brain_service_init_happy_path():
    remote_brain = RemoteBrainService()
    assert remote_brain.neural_engine_url == f"http://127.0.0.1:{PORTS.NEURAL_ENGINE}"
    assert remote_brain.tokenizer is None
    assert remote_brain.model == "Remote: gpt-3.5-turbo"
    assert mock_logger_info.call_count == 1

@pytest.mark.usefixtures('mock_os_env', 'mock_logger_info', 'mock_settings_base_model_name')
def test_remote_brain_service_init_with_custom_neural_engine_url():
    with patch('os.getenv', return_value="http://custom-server:8080"):
        remote_brain = RemoteBrainService()
        assert remote_brain.neural_engine_url == "http://custom-server:8080"

@pytest.mark.usefixtures('mock_os_env', 'mock_logger_info', 'mock_settings_base_model_name')
def test_remote_brain_service_init_with_empty_env_variable():
    with patch('os.getenv', return_value=""):
        remote_brain = RemoteBrainService()
        assert remote_brain.neural_engine_url == f"http://127.0.0.1:{PORTS.NEURAL_ENGINE}"

@pytest.mark.usefixtures('mock_os_env', 'mock_logger_info', 'mock_settings_base_model_name')
def test_remote_brain_service_init_with_none_env_variable():
    with patch('os.getenv', return_value=None):
        remote_brain = RemoteBrainService()
        assert remote_brain.neural_engine_url == f"http://127.0.0.1:{PORTS.NEURAL_ENGINE}"

@pytest.mark.usefixtures('mock_os_env', 'mock_logger_info', 'mock_settings_base_model_name')
def test_remote_brain_service_init_with_invalid_port_env_variable():
    with patch('os.getenv', return_value="http://127.0.0.1:not_a_port"):
        with pytest.raises(ValueError):
            RemoteBrainService()

@pytest.mark.usefixtures('mock_os_env', 'mock_logger_info', 'mock_settings_base_model_name')
def test_remote_brain_service_init_with_invalid_protocol_env_variable():
    with patch('os.getenv', return_value="ftp://127.0.0.1:8080"):
        with pytest.raises(ValueError):
            RemoteBrainService()