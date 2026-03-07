import pytest
from unittest.mock import Mock, patch
from gateway.app.ml.ml_tools import MLTools

@pytest.fixture()
def ml_tools():
    return MLTools(data_dir="test_data_dir")

@patch('gateway.app.ml.ml_tools.HFDataManager')
@patch('gateway.app.ml.ml_tools.ModelTrainer')
@patch('gateway.app.ml.ml_tools.ExperimentManager')
def test_train_text_classifier_happy_path(mlm, mt, em, ml_tools):
    # Mock objects
    dataset = Mock()
    result = {"success": True, "metrics": {"accuracy": 0.9}, "model_path": "test_model_path"}
    experiment_id = "test_experiment_id"

    # Patch return values
    mlm.return_value.load_dataset.return_value = dataset
    mt.return_value.train_classification_model.return_value = result
    em.return_value.create_experiment.return_value = experiment_id
    em.return_value.log_training_run.return_value = None

    # Call the function
    output = ml_tools.train_text_classifier("test_dataset", "bert-base-uncased", config={"text_column": "text"})

    # Assertions
    assert output == {"success": True, "metrics": {"accuracy": 0.9}, "model_path": "test_model_path"}
    mlm.return_value.load_dataset.assert_called_once_with("test_dataset", split="train")
    mt.return_value.train_classification_model.assert_called_once_with(
        dataset=dataset,
        model_name="bert-base-uncased",
        text_column="text",
        label_column="label",
        config=None
    )
    em.return_value.create_experiment.assert_called_once_with(f"train_test_dataset")
    em.return_value.log_training_run.assert_called_once_with(
        experiment_id=experiment_id,
        run_name="run_bert-base-uncased",
        parameters={"model": "bert-base-uncased", "dataset": "test_dataset"},
        metrics={"accuracy": 0.9},
        artifacts={"model": "test_model_path"},
        model_info={"task_type": "classification", "model_name": "bert-base-uncased"}
    )

@patch('gateway.app.ml.ml_tools.HFDataManager')
def test_train_text_classifier_edge_case_none_dataset(mlm, ml_tools):
    # Mock objects
    result = {"success": True, "metrics": {"accuracy": 0.9}, "model_path": "test_model_path"}

    # Patch return values
    mlm.return_value.load_dataset.return_value = None

    # Call the function
    output = ml_tools.train_text_classifier("test_dataset", "bert-base-uncased", config={"text_column": "text"})

    # Assertions
    assert output == {"success": False, "error": "Failed to load dataset"}
    mlm.return_value.load_dataset.assert_called_once_with("test_dataset", split="train")

@patch('gateway.app.ml.ml_tools.HFDataManager')
def test_train_text_classifier_error_case_invalid_config(mlm, ml_tools):
    # Mock objects
    result = {"success": True, "metrics": {"accuracy": 0.9}, "model_path": "test_model_path"}

    # Patch return values
    mlm.return_value.load_dataset.return_value = Mock()
    mt.return_value.train_classification_model.return_value = result

    # Call the function
    output = ml_tools.train_text_classifier("test_dataset", "bert-base-uncased", config={"invalid_key": "value"})

    # Assertions
    assert output == {"success": False, "error": "Invalid configuration key: 'invalid_key'"}
    mlm.return_value.load_dataset.assert_called_once_with("test_dataset", split="train")