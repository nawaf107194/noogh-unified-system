import pytest
from pathlib import Path
from typing import Dict, List

from neural_engine.knowledge_cache import KnowledgeCache

@pytest.fixture
def default_data_dir():
    return "/home/noogh/projects/noogh_unified_system/src/training_data"

def test_happy_path(default_data_dir):
    cache = KnowledgeCache(data_dir=default_data_dir)
    assert cache.data_dir == Path(default_data_dir)
    assert cache.knowledge == {
        'category1': [],
        'category2': [],
        # Add more categories if defined in the class
    }
    assert not cache.loaded
    assert cache.total_samples == 0

def test_edge_case_none():
    with pytest.raises(TypeError) as exc_info:
        KnowledgeCache(data_dir=None)
    assert str(exc_info.value) == "data_dir cannot be None"

def test_edge_case_empty_string():
    with pytest.raises(ValueError) as exc_info:
        KnowledgeCache(data_dir='')
    assert str(exc_info.value) == "data_dir cannot be an empty string"

def test_invalid_input_type():
    with pytest.raises(TypeError) as exc_info:
        KnowledgeCache(data_dir=123)
    assert str(exc_info.value) == "data_dir must be a string"