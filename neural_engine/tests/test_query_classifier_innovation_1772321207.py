import pytest

from neural_engine.query_classifier import QueryClassifier

def test_get_classification_details_happy_path():
    classifier = QueryClassifier()
    query = "What is 2 + 2?"
    result = classifier.get_classification_details(query)
    assert result == {
        "query": query,
        "classification": classifier.classify(query),
        "is_mathematical": True,
        "requires_strict": False,
        "detected_keywords": ["math", "addition"]
    }

def test_get_classification_details_empty_query():
    classifier = QueryClassifier()
    result = classifier.get_classification_details("")
    assert result == {
        "query": "",
        "classification": classifier.classify(""),
        "is_mathematical": False,
        "requires_strict": False,
        "detected_keywords": []
    }

def test_get_classification_details_none_query():
    classifier = QueryClassifier()
    result = classifier.get_classification_details(None)
    assert result == {
        "query": None,
        "classification": classifier.classify(None),
        "is_mathematical": False,
        "requires_strict": False,
        "detected_keywords": []
    }

def test_get_classification_details_boundary_query():
    classifier = QueryClassifier()
    query = "2 + 2"
    result = classifier.get_classification_details(query)
    assert result == {
        "query": query,
        "classification": classifier.classify(query),
        "is_mathematical": True,
        "requires_strict": False,
        "detected_keywords": ["math", "addition"]
    }

# Assuming classify() and is_mathematical() do not raise exceptions for invalid inputs