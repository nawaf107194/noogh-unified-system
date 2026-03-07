import pytest
from datasets import Dataset
from typing import Optional, Dict

class MockHFDataManager:
    def __init__(self):
        self.task_type_cache = {}

    def _infer_task_type(self, dataset: Dataset, label_column: Optional[str]) -> str:
        if "binary" in dataset.column_names and label_column == "label":
            return "binary_classification"
        elif "text" in dataset.column_names and label_column is None:
            return "text_classification"
        else:
            return "unknown"

    def prepare_training_data(
        self,
        dataset: Dataset,
        text_column: str = "text",
        label_column: Optional[str] = None,
        max_samples: Optional[int] = None,
    ) -> Dict:
        total_samples = len(dataset)
        columns = dataset.column_names
        sample_data = {}
        if total_samples > 0:
            sample = dataset[0]
            for key in list(sample.keys())[:3]:
                if isinstance(sample[key], (str, int, float)):
                    sample_data[key] = str(sample[key])[:100]

        task_type = self._infer_task_type(dataset, label_column)
        return {
            "success": True,
            "task_type": task_type,
            "stats": {"total_samples": total_samples, "columns": columns, "sample_data": sample_data},
        }

@pytest.fixture
def hf_data_manager():
    return MockHFDataManager()

def test_prepare_training_data_happy_path(hf_data_manager):
    dataset = Dataset.from_dict({
        "text": ["This is a sample text.", "Another example here."],
        "label": [0, 1]
    })
    result = hf_data_manager.prepare_training_data(dataset)
    assert result == {
        "success": True,
        "task_type": "binary_classification",
        "stats": {
            "total_samples": 2,
            "columns": ["text", "label"],
            "sample_data": {"text": "This is a sample tex", "label": "0"}
        }
    }

def test_prepare_training_data_empty_dataset(hf_data_manager):
    dataset = Dataset.from_dict({})
    result = hf_data_manager.prepare_training_data(dataset)
    assert result == {
        "success": True,
        "task_type": "unknown",
        "stats": {
            "total_samples": 0,
            "columns": [],
            "sample_data": {}
        }
    }

def test_prepare_training_data_no_label_column(hf_data_manager):
    dataset = Dataset.from_dict({
        "text": ["Sample text."]
    })
    result = hf_data_manager.prepare_training_data(dataset)
    assert result == {
        "success": True,
        "task_type": "text_classification",
        "stats": {
            "total_samples": 1,
            "columns": ["text"],
            "sample_data": {"text": "Sample tex"}
        }
    }

def test_prepare_training_data_invalid_label_column(hf_data_manager):
    dataset = Dataset.from_dict({
        "text": ["Sample text."]
    })
    result = hf_data_manager.prepare_training_data(dataset, label_column="label")
    assert result == {
        "success": True,
        "task_type": "unknown",
        "stats": {
            "total_samples": 1,
            "columns": ["text"],
            "sample_data": {"text": "Sample tex"}
        }
    }

# Note: There are no explicit error cases in the provided code, so we don't need additional tests for that.