import pytest

class MetaCognitionModuleTest:

    def test_happy_path(self):
        # Test with normal inputs
        obj = MetaCognitionModule(0.8)
        assert obj.confidence_threshold == 0.8
        assert isinstance(obj.logger, logging.Logger)

    @pytest.mark.parametrize("input_value", [None, "", -1, 2, "string"])
    def test_edge_cases(self, input_value):
        # Test with edge cases
        if input_value is None:
            obj = MetaCognitionModule(None)
            assert obj.confidence_threshold == 0.8
        else:
            with pytest.raises(ValueError) as exc_info:
                MetaCognitionModule(input_value)
            assert str(exc_info.value) == "Invalid confidence threshold"

    def test_error_case(self):
        # Test with invalid input that raises an exception
        with pytest.raises(ValueError) as exc_info:
            MetaCognitionModule(-1)
        assert str(exc_info.value) == "Invalid confidence threshold"