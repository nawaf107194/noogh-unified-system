import pytest
from unittest.mock import patch, MagicMock
from typing import Optional, Dict
from gateway.app.ml.ml_tools import HFDataManager

# Mocking the HFDataManager class
class MockHFDataManager(HFDataManager):
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.dataset = ["mock_data"] * 100  # Mock dataset with 100 rows

    def load_dataset(self, dataset_name, config_name=None, split="train"):
        return self.dataset

    def prepare_training_data(self, dataset, text_column="text", label_column=None):
        return {"num_rows": len(dataset), "text_column": text_column, "label_column": label_column}

@pytest.fixture
def ml_tool_instance():
    class MLToolInstance:
        def __init__(self, data_dir):
            self.data_dir = data_dir
            self.mgr = MockHFDataManager(data_dir)
        
        def load_and_analyze_dataset(self, dataset_name: str, config: Optional[Dict] = None) -> Dict:
            try:
                cfg_name = config.get("config_name") if config else None
                split = config.get("split", "train") if config else "train"

                dataset = self.mgr.load_dataset(dataset_name, config_name=cfg_name, split=split)
                analysis = self.mgr.prepare_training_data(
                    dataset,
                    text_column=config.get("text_column", "text") if config else "text",
                    label_column=config.get("label_column") if config else None,
                )
                return {"success": True, "dataset_name": dataset_name, "rows": len(dataset), "analysis": analysis}
            except Exception as e:
                return {"success": False, "error": str(e)}
    
    return MLToolInstance("/path/to/data")

# Test cases
def test_happy_path(ml_tool_instance):
    result = ml_tool_instance.load_and_analyze_dataset("example_dataset")
    assert result["success"]
    assert result["dataset_name"] == "example_dataset"
    assert result["rows"] == 100
    assert result["analysis"]["num_rows"] == 100

def test_with_config(ml_tool_instance):
    config = {"config_name": "default", "split": "test", "text_column": "text", "label_column": "label"}
    result = ml_tool_instance.load_and_analyze_dataset("example_dataset", config)
    assert result["success"]
    assert result["analysis"]["text_column"] == "text"
    assert result["analysis"]["label_column"] == "label"

def test_empty_config(ml_tool_instance):
    result = ml_tool_instance.load_and_analyze_dataset("example_dataset", {})
    assert result["success"]
    assert result["analysis"]["text_column"] == "text"
    assert result["analysis"]["label_column"] is None

def test_none_config(ml_tool_instance):
    result = ml_tool_instance.load_and_analyze_dataset("example_dataset", None)
    assert result["success"]
    assert result["analysis"]["text_column"] == "text"
    assert result["analysis"]["label_column"] is None

def test_invalid_dataset_name(ml_tool_instance):
    with patch.object(MockHFDataManager, 'load_dataset', side_effect=ValueError("Invalid dataset name")):
        result = ml_tool_instance.load_and_analyze_dataset("invalid_dataset")
        assert not result["success"]
        assert "Invalid dataset name" in result["error"]

def test_async_behavior_not_applicable(ml_tool_instance):
    # Since the function does not have async behavior, this test is more of a placeholder.
    pass