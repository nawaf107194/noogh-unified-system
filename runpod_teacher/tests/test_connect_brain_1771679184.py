import pytest

from runpod_teacher.connect_brain_1771679184 import ConnectionStrategy, connect_brain_1771679184

class TestConnectionStrategy:
    def test_happy_path(self, strategy):
        # Arrange
        expected_strategy = strategy
        
        # Act
        instance = connect_brain_1771679184(strategy)
        
        # Assert
        assert instance._strategy == expected_strategy
    
    @pytest.mark.parametrize("invalid_input", [None, [], "string", 123])
    def test_error_cases(self, invalid_input):
        # Arrange & Act
        with pytest.raises(TypeError) as e:
            instance = connect_brain_1771679184(invalid_input)
        
        # Assert
        assert str(e.value) == "Expected a ConnectionStrategy object"