import pytest

class MockConfidenceCalibration:
    def __init__(self):
        self.confidence = 0.6

    def update_confidence(self, action, result):
        if action == "success":
            self.confidence += 0.1
        elif action == "failure":
            self.confidence -= 0.1
        return self.confidence

@pytest.fixture
def calibration():
    return MockConfidenceCalibration()

def test_happy_path(calibration):
    assert calibration.get_confidence_threshold("success") == 0.75
    assert calibration.get_confidence_threshold("failure") == 0.5
    assert calibration.get_confidence_threshold("unknown") == 0.6

def test_edge_cases(calibration):
    calibration.confidence = 0.8
    assert calibration.get_confidence_threshold("success") == 0.9
    calibration.confidence = 0.4
    assert calibration.get_confidence_threshold("failure") == 0.3
    calibration.confidence = 1.0
    assert calibration.get_confidence_threshold("success") == 1.0
    calibration.confidence = 0.0
    assert calibration.get_confidence_threshold("failure") == -0.1

def test_error_cases(calibration):
    # Since the function does not raise any exceptions, these tests are skipped.
    pass

# If this were an async function, you would need to use pytest-asyncio and await the results.