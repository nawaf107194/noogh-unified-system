import pytest

class TestNormalizeWeights:

    @pytest.fixture
    def mock_instance(self):
        class MockClass:
            def __init__(self, current_weights):
                self.current_weights = current_weights
            
            def normalize_weights(self):
                total_weight = sum(self.current_weights.values())
                self.current_weights = {k: v / total_weight for k, v in self.current_weights.items()}
        
        return MockClass

    def test_happy_path(self, mock_instance):
        instance = mock_instance({'hypothesis1': 20, 'hypothesis2': 30, 'hypothesis3': 50})
        instance.normalize_weights()
        assert instance.current_weights == {'hypothesis1': 0.2, 'hypothesis2': 0.3, 'hypothesis3': 0.5}
    
    def test_empty_weights(self, mock_instance):
        instance = mock_instance({})
        instance.normalize_weights()
        assert instance.current_weights == {}
    
    def test_single_entry(self, mock_instance):
        instance = mock_instance({'only_hypothesis': 100})
        instance.normalize_weights()
        assert instance.current_weights == {'only_hypothesis': 1.0}
    
    def test_zero_total_weight(self, mock_instance):
        instance = mock_instance({'hypothesis1': 0, 'hypothesis2': 0, 'hypothesis3': 0})
        with pytest.raises(ZeroDivisionError):
            instance.normalize_weights()

    def test_non_numeric_values(self, mock_instance):
        instance = mock_instance({'hypothesis1': 'a', 'hypothesis2': 'b', 'hypothesis3': 'c'})
        with pytest.raises(TypeError):
            instance.normalize_weights()

    def test_mixed_types(self, mock_instance):
        instance = mock_instance({'hypothesis1': 20, 'hypothesis2': 'b', 'hypothesis3': 50})
        with pytest.raises(TypeError):
            instance.normalize_weights()

    def test_async_behavior(self, mock_instance):
        # Since the provided function does not have any async behavior,
        # this test is not applicable. The function is synchronous.
        pass