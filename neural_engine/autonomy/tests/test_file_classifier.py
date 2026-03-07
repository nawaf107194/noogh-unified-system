import pytest
from typing import Dict

class MockFileClassifier:
    def analyze_file(self, filepath: str):
        """Mock method to return a dummy proposal."""
        class Proposal:
            def __init__(self, current_category, proposed_category, confidence, reasons, requires_review):
                self.current_category = current_category
                self.proposed_category = proposed_category
                self.confidence = confidence
                self.reasons = reasons
                self.requires_review = requires_review

        return Proposal(
            FileCategory.IMAGE,
            FileCategory.DOCUMENT,
            0.85,
            ["Reason1", "Reason2"],
            False
        )

class FileCategory:
    IMAGE = "image"
    DOCUMENT = "document"
    UNKNOWN = "unknown"

def test_propose_single_happy_path(mocker):
    classifier = MockFileClassifier()
    file_classifier_instance = NeuralEngineAutonomy(file_classifier=classifier)
    
    result = file_classifier_instance.propose_single("/path/to/image.jpg")
    
    assert result == {
        "filepath": "/path/to/image.jpg",
        "current_category": FileCategory.IMAGE,
        "proposed_category": FileCategory.DOCUMENT,
        "confidence": 0.85,
        "confidence_label": classifier._confidence_label(0.85),
        "reasons": ["Reason1", "Reason2"],
        "requires_review": False,
        "status": "proposed"
    }

def test_propose_single_edge_case_empty_filepath():
    classifier = MockFileClassifier()
    file_classifier_instance = NeuralEngineAutonomy(file_classifier=classifier)
    
    result = file_classifier_instance.propose_single("")
    
    assert result == {
        "filepath": "",
        "current_category": FileCategory.UNKNOWN,
        "proposed_category": FileCategory.UNKNOWN,
        "confidence": 0.0,
        "confidence_label": classifier._confidence_label(0.0),
        "reasons": [],
        "requires_review": False,
        "status": "uncertain"
    }

def test_propose_single_edge_case_none_filepath():
    classifier = MockFileClassifier()
    file_classifier_instance = NeuralEngineAutonomy(file_classifier=classifier)
    
    result = file_classifier_instance.propose_single(None)
    
    assert result == {
        "filepath": None,
        "current_category": FileCategory.UNKNOWN,
        "proposed_category": FileCategory.UNKNOWN,
        "confidence": 0.0,
        "confidence_label": classifier._confidence_label(0.0),
        "reasons": [],
        "requires_review": False,
        "status": "uncertain"
    }

def test_propose_single_error_case_invalid_filepath():
    with pytest.raises(FileNotFoundError):
        classifier = MockFileClassifier()
        file_classifier_instance = NeuralEngineAutonomy(file_classifier=classifier)
        
        result = file_classifier_instance.propose_single("/path/to/nonexistent/file.jpg")