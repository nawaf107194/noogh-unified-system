import pytest
from unittest.mock import patch, mock_open
import os

from gateway.app.llm.remote_brain import RemoteBrainService
from config.ports import PORTS
from settings import settings

@pytest.fixture
def remote_brain_service():
    with patch.dict(os.environ, {"NEURAL_ENGINE_URL": None}):
        return RemoteBrainService()

@pytest.mark.parametrize("neural_engine_url", [None, "", "http://example.com"])
def test_neural_engine_url(remote_brain_service, neural_engine_url):
    if neural_engine_url is None:
        os.environ["NEURAL_ENGINE_URL"] = ""
    else:
        os.environ["NEURAL_ENGINE_URL"] = neural_engine_url
    
    service = RemoteBrainService()
    assert service.neural_engine_url == neural_engine_url

def test_model_attribute(remote_brain_service):
    assert remote_brain_service.model == f"Remote: {settings.BASE_MODEL_NAME}"

def test_tokenizer_attribute(remote_brain_service):
    assert remote_brain_service.tokenizer is None

def test_logger_info(mocker):
    with patch('gateway.app.llm.remote_brain.logger.info') as mock_info:
        service = RemoteBrainService()
        mock_info.assert_called_once_with(f"Initialized RemoteBrainService pointing to http://127.0.0.1:{PORTS.NEURAL_ENGINE}")