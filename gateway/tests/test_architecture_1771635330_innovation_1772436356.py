import pytest

from gateway.architecture_1771635330 import create_model, Evaluator, Curriculum, DreamWorker

class TestCreateModel:

    def test_happy_path_evaluator(self):
        model = create_model("evaluator", param="value")
        assert isinstance(model, Evaluator)
        assert model.param == "value"

    def test_happy_path_curriculum(self):
        model = create_model("curriculum", param="value")
        assert isinstance(model, Curriculum)
        assert model.param == "value"

    def test_happy_path_dream_worker(self):
        model = create_model("dream_worker", param="value")
        assert isinstance(model, DreamWorker)
        assert model.param == "value"

    def test_edge_case_empty_input(self):
        with pytest.raises(ValueError) as exc_info:
            create_model("")
        assert str(exc_info.value) == "Unknown model type: "

    def test_edge_case_none_input(self):
        with pytest.raises(ValueError) as exc_info:
            create_model(None)
        assert str(exc_info.value) == "Unknown model type: None"

    def test_error_case_invalid_input(self):
        with pytest.raises(ValueError) as exc_info:
            create_model("invalid_type")
        assert str(exc_info.value) == "Unknown model type: invalid_type"