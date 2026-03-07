import pytest
from unified_core.neural_bridge import NeuralRequest, _inflict_scar
from unified_core.core.scar import Failure
import hashlib
import time
import logging

# Mock logger to capture output
class MockLogger:
    def __init__(self):
        self.output = []

    def warning(self, msg):
        self.output.append(msg)

    def debug(self, msg):
        self.output.append(msg)

logger = MockLogger()

# Monkey patch the real logger with our mock
_neural_bridge_logger = logging.getLogger(__name__)
_neural_bridge_logger.warning = logger.warning
_neural_bridge_logger.debug = logger.debug

def test_inflict_scar_happy_path():
    request = NeuralRequest(request_id="12345", query="test query")
    _inflict_scar(request, "Error occurred")
    assert len(logger.output) == 1
    assert "Neural unknown failure scarred" in logger.output[0]
    failure_id = hash("neural_unknown:12345:" + str(time.time())).hexdigest()[:16]
    assert failure_id in logger.output[0]

def test_inflict_scar_empty_request():
    request = NeuralRequest(request_id="", query="")
    _inflict_scar(request, "Error occurred")
    assert len(logger.output) == 1
    assert "Neural unknown failure scarred" in logger.output[0]
    failure_id = hash("neural_unknown::" + str(time.time())).hexdigest()[:16]
    assert failure_id in logger.output[0]

def test_inflict_scar_none_request():
    _inflict_scar(None, "Error occurred")
    assert len(logger.output) == 1
    assert "Neural unknown failure scarred" in logger.output[0]
    failure_id = hash("neural_unknown:None:" + str(time.time())).hexdigest()[:16]
    assert failure_id in logger.output[0]

def test_inflict_scar_boundary_request():
    request = NeuralRequest(request_id="1" * 128, query="a" * 256)
    _inflict_scar(request, "Error occurred")
    assert len(logger.output) == 1
    assert "Neural unknown failure scarred" in logger.output[0]
    failure_id = hash("neural_unknown:" + ("1" * 128) + ":" + str(time.time())).hexdigest()[:16]
    assert failure_id in logger.output[0]

def test_inflict_scar_invalid_severity():
    request = NeuralRequest(request_id="12345", query="test query")
    _inflict_scar(request, "Error occurred", severity="invalid")
    assert len(logger.output) == 1
    assert "Neural unknown failure scarred" in logger.output[0]
    failure_id = hash("neural_unknown:12345:" + str(time.time())).hexdigest()[:16]
    assert failure_id in logger.output[0]

def test_inflict_scar_failure_tissue_none():
    request = NeuralRequest(request_id="12345", query="test query")
    _inflict_scar(request, "Error occurred", severity=None)
    assert len(logger.output) == 1
    assert "Neural unknown failure scarred" in logger.output[0]
    failure_id = hash("neural_unknown:12345:" + str(time.time())).hexdigest()[:16]
    assert failure_id in logger.output[0]

def test_inflict_scar_no_logger():
    request = NeuralRequest(request_id="12345", query="test query")
    def mock_logger(*args, **kwargs):
        pass
    _inflict_scar(request, "Error occurred", severity=None)
    assert len(logger.output) == 0

def test_inflict_scar_failure_tissue_error():
    request = NeuralRequest(request_id="12345", query="test query")
    class MockScarTissue:
        def inflict(self, failure):
            raise Exception("Simulated scar infliction error")

    _inflict_scar(request, "Error occurred", severity=None)
    assert len(logger.output) == 1
    assert "Scar infliction failed" in logger.output[0]