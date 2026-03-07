import pytest

class MockMemory():
    def retrieve_similar_actions(self, action):
        if action == 'valid_action':
            return ['success', 'failure', 'success']
        elif action == 'empty_history':
            return []
        elif action is None:
            return None
        else:
            raise ValueError(f"Unexpected action: {action}")

class TestConfidenceCalibration():
    def setup_method(self):
        self.memory = MockMemory()
        from unified_core.intelligence.confidence_calibration import ConfidenceCalibration
        self.calibrator = ConfidenceCalibration(memory=self.memory)

    @pytest.mark.parametrize("action, outcome, expected", [
        ('valid_action', 'success', 0.9),
        ('valid_action', 'failure', 0.3),
        ('empty_history', 'success', 0.5),
        (None, 'success', 0.5)
    ])
    def test_happy_path(self, action, outcome, expected):
        result = self.calibrator.update_confidence(action, outcome)
        assert result == expected

    @pytest.mark.parametrize("action, outcome", [
        ('invalid_action', 'success'),
        ('valid_action', None),
        (None, None)
    ])
    def test_error_cases(self, action, outcome):
        with pytest.raises(ValueError):
            self.calibrator.update_confidence(action, outcome)

    def test_async_behavior(self, monkeypatch):
        async def mock_memory_retrieve_similar_actions(action):
            return ['success', 'failure', 'success']
        
        monkeypatch.setattr(MockMemory, "retrieve_similar_actions", mock_memory_retrieve_similar_actions)
        
        result = self.calibrator.update_confidence('valid_action', 'success')
        assert result == 0.9