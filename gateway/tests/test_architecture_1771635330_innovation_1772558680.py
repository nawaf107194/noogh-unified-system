import pytest
from gateway.architecture_1771635330 import create_model
from evaluator import Evaluator
from curriculum import Curriculum
from dream_worker import DreamWorker

@pytest.fixture
def evaluator_model():
    return create_model("evaluator", some_arg=1)

@pytest.fixture
def curriculum_model():
    return create_model("curriculum", some_arg=2)

@pytest.fixture
def dream_worker_model():
    return create_model("dream_worker", some_arg=3)

def test_create_model_evaluator(evaluator_model):
    assert isinstance(evaluator_model, Evaluator)

def test_create_model_curriculum(curriculum_model):
    assert isinstance(curriculum_model, Curriculum)

def test_create_model_dream_worker(dream_worker_model):
    assert isinstance(dream_worker_model, DreamWorker)

def test_create_model_invalid_type():
    with pytest.raises(ValueError, match="Unknown model type"):
        create_model("invalid_type")

def test_create_model_empty_type():
    with pytest.raises(ValueError, match="Unknown model type"):
        create_model("")

def test_create_model_none_type():
    with pytest.raises(ValueError, match="Unknown model type"):
        create_model(None)

def test_create_model_unexpected_case():
    with pytest.raises(ValueError, match="Unknown model type"):
        create_model("Evaluator")