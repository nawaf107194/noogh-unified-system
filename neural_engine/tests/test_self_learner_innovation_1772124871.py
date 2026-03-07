import pytest

from neural_engine.self_learner import learn_from_react_result, get_learner

class MockLearner:
    def __init__(self):
        self.learned_conversations = []
        self.extracted_knowledges = []

    def learn_from_conversation(self, query: str, response: str, success: bool, metadata: dict):
        self.learned_conversations.append((query, response, success, metadata))

    def extract_knowledge(self, text: str, source: str):
        self.extracted_knowledges.append((text, source))

def test_learn_from_react_result_happy_path():
    learner = MockLearner()
    get_learner.return_value = learner

    query = "What is the capital of France?"
    result = {"answer": "Paris"}
    learn_from_react_result(query, result)

    assert learner.learned_conversations == [
        (query, "Paris", True, {
            "iterations": 0,
            "tool_calls": 0,
            "confidence": 0.5
        })
    ]
    assert learner.extracted_knowledges == [
        ("What is the capital of France?", "user_query"),
        ("Paris", "model_response")
    ]

def test_learn_from_react_result_empty_result():
    learner = MockLearner()
    get_learner.return_value = learner

    query = "What is the capital of France?"
    result = {}
    learn_from_react_result(query, result)

    assert not learner.learned_conversations
    assert not learner.extracted_knowledges

def test_learn_from_react_result_none_result():
    learner = MockLearner()
    get_learner.return_value = learner

    query = "What is the capital of France?"
    result = None
    learn_from_react_result(query, result)

    assert not learner.learned_conversations
    assert not learner.extracted_knowledges

def test_learn_from_react_result_error_case():
    learner = MockLearner()
    get_learner.return_value = learner

    query = "What is the capital of France?"
    result = {"answer": ""}
    learn_from_react_result(query, result, success=False)

    assert not learner.learned_conversations
    assert learner.extracted_knowledges == [
        ("What is the capital of France?", "user_query")
    ]

def test_learn_from_react_result_invalid_input():
    with pytest.raises(TypeError):
        learn_from_react_result(123, {})