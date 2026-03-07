import pytest
from unittest.mock import patch, mock_open
from datetime import datetime
import json

from neural_engine.self_learner import SelfLearner

@pytest.fixture
def self_learner(tmpdir):
    return SelfLearner(knowledge_file=tmpdir.join("knowledge.json").strpath)

@patch('neural_engine.self_learner.datetime.now')
def test_happy_path(mock_datetime, self_learner):
    mock_datetime.return_value = datetime(2023, 10, 1, 12, 0, 0)
    
    text = "أنا محمد. أعرف أن الشمس هي الكوكب الأقرب للنجمة الشمسية."
    self_learner.extract_knowledge(text)
    
    with open(self_learner.knowledge_file, 'r', encoding='utf-8') as f:
        entries = [json.loads(line) for line in f]
    
    assert len(entries) == 2
    assert entries[0] == {
        "id": self_learner._generate_id("أنا محمد"),
        "timestamp": "2023-10-01T12:00:00",
        "content": "أنا محمد",
        "type": "user_info",
        "source": "conversation",
        "verified": False
    }
    assert entries[1] == {
        "id": self_learner._generate_id("الشمس هي الكوكب الأقرب للنجمة الشمسية"),
        "timestamp": "2023-10-01T12:00:00",
        "content": "الشمس هي الكوكب الأقرب للنجمة الشمسية",
        "type": "fact",
        "source": "conversation",
        "verified": False
    }

def test_empty_text(self_learner):
    self_learner.extract_knowledge("")
    with open(self_learner.knowledge_file, 'r', encoding='utf-8') as f:
        entries = [json.loads(line) for line in f]
    
    assert len(entries) == 0

def test_none_text(self_learner):
    self_learner.extract_knowledge(None)
    with open(self_learner.knowledge_file, 'r', encoding='utf-8') as f:
        entries = [json.loads(line) for line in f]
    
    assert len(entries) == 0

def test_boundary_text_length(self_learner):
    text = "X" * 15
    self_learner.extract_knowledge(text)
    with open(self_learner.knowledge_file, 'r', encoding='utf-8') as f:
        entries = [json.loads(line) for line in f]
    
    assert len(entries) == 0

def test_invalid_input_type(self_learner):
    with pytest.raises(TypeError):
        self_learner.extract_knowledge(123)