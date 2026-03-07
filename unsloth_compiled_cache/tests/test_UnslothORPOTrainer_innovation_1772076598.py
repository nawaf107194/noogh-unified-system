import pytest

from unsloth_compiled_cache.UnslothORPOTrainer import UnslothORPOTrainer
from typing import Literal, Dict

def create_dummy_trainer():
    return UnslothORPOTrainer()

@pytest.fixture
def trainer():
    return create_dummy_trainer()

@pytest.mark.parametrize("metrics, train_eval, expected", [
    ({"accuracy": 0.95}, "train", {"train": {"accuracy": [0.95]}}),
    ({"loss": 0.2}, "eval", {"train": {}, "eval": {"loss": [0.2]}}),
    ({"accuracy": 0.8, "loss": 0.15}, "train", {"train": {"accuracy": [0.95, 0.8], "loss": [None]}, "eval": {}})
])
def test_store_metrics_happy_path(trainer, metrics, train_eval, expected):
    trainer.store_metrics(metrics, train_eval)
    assert trainer._stored_metrics == expected

@pytest.mark.parametrize("metrics, train_eval", [
    ({}, "train"),
    (None, "eval"),
    ({"accuracy": 0.95}, None),
    ({"accuracy": 0.95}, "test")
])
def test_store_metrics_edge_cases(trainer, metrics, train_eval):
    trainer.store_metrics(metrics, train_eval)
    assert trainer._stored_metrics == {}

@pytest.mark.parametrize("metrics, train_eval", [
    ([], "train"),
    ((1, 2), "eval"),
    ({None: None}, "train")
])
def test_store_metrics_error_cases(trainer, metrics, train_eval):
    trainer.store_metrics(metrics, train_eval)
    assert trainer._stored_metrics == {}

# Assuming the function does not have async behavior