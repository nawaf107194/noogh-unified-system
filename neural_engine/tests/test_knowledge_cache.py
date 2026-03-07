import pytest
from pathlib import Path
import json

from neural_engine.knowledge_cache import KnowledgeCache

@pytest.fixture
def knowledge_cache(tmp_path):
    cache = KnowledgeCache()
    cache.data_dir = tmp_path
    return cache

def test_load_dataset_happy_path(knowledge_cache, caplog):
    dataset_path = knowledge_cache.data_dir / "NOOGH_ULTIMATE_DATASET.jsonl"
    
    # Create a sample JSONL file
    with open(dataset_path, "w", encoding="utf-8") as f:
        f.write('{"category": "math", "instruction": "Add 2 and 3", "input": "", "output": "5"}\n')
        f.write('{"category": "science", "instruction": "What is the capital of France?", "input": "", "output": "Paris"}\n')
    
    knowledge_cache.load_dataset()
    
    assert knowledge_cache.knowledge == {
        "math": [{"instruction": "Add 2 and 3", "input": "", "output": "5"}],
        "science": [{"instruction": "What is the capital of France?", "input": "", "output": "Paris"}]
    }
    assert knowledge_cache.total_samples == 2
    assert "✅ Loaded 2 knowledge samples" in caplog.text

def test_load_dataset_empty_file(knowledge_cache, caplog):
    dataset_path = knowledge_cache.data_dir / "NOOGH_ULTIMATE_DATASET.jsonl"
    
    # Create an empty JSONL file
    with open(dataset_path, "w", encoding="utf-8") as f:
        pass
    
    knowledge_cache.load_dataset()
    
    assert len(knowledge_cache.knowledge) == 0
    assert knowledge_cache.total_samples == 0
    assert "Dataset not found" in caplog.text

def test_load_dataset_invalid_json(knowledge_cache, caplog):
    dataset_path = knowledge_cache.data_dir / "NOOGH_ULTIMATE_DATASET.jsonl"
    
    # Create a file with invalid JSON
    with open(dataset_path, "w", encoding="utf-8") as f:
        f.write('{"category": "math", "instruction": "Add 2 and 3", "input": "", "output": "5"\n')
    
    knowledge_cache.load_dataset()
    
    assert len(knowledge_cache.knowledge) == 0
    assert knowledge_cache.total_samples == 0
    assert "Error loading dataset" in caplog.text

def test_load_dataset_max_per_category_limit(knowledge_cache, caplog):
    dataset_path = knowledge_cache.data_dir / "NOOGH_ULTIMATE_DATASET.jsonl"
    
    # Create a sample JSONL file with more than max_per_category entries
    with open(dataset_path, "w", encoding="utf-8") as f:
        for i in range(150):
            f.write(f'{{"category": "math{i%2}", "instruction": "Add {i} and 3", "input": "", "output": "{i+3}"}}\n')
    
    knowledge_cache.load_dataset(max_per_category=100)
    
    assert len(knowledge_cache.knowledge["math0"]) == 50
    assert len(knowledge_cache.knowledge["math1"]) == 50
    assert knowledge_cache.total_samples == 100