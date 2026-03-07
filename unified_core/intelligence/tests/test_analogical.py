import pytest
from unified_core.intelligence.analogical import Analogical, AnalogyMatch

class MockKBItem:
    def __init__(self, domain, structure, solution):
        self.domain = domain
        self.structure = structure
        self.solution = solution

@pytest.fixture
def analogical():
    return Analogical()

@pytest.fixture
def mock_kb():
    items = [
        MockKBItem("Software Engineering", {"A": "B"}, "Refactor"),
        MockKBItem("Manufacturing", {"X": "Y"}, "Reorganize"),
        MockKBItem("Education", {"P": "Q"}, "Revise")
    ]
    return items

def test_find_analogies_happy_path(analogical, mock_kb):
    analogical.knowledge_base = mock_kb
    current_situation_desc = "Refactor the codebase"
    
    result = analogical.find_analogies(current_situation_desc)
    
    assert len(result) == 3
    for match in result:
        assert isinstance(match, AnalogyMatch)

def test_find_analogies_empty_knowledge_base(analogical):
    analogical.knowledge_base = []
    current_situation_desc = "Refactor the codebase"
    
    result = analogical.find_analogies(current_situation_desc)
    
    assert len(result) == 0

def test_find_analogies_none_current_situation_desc(analogical, mock_kb):
    analogical.knowledge_base = mock_kb
    current_situation_desc = None
    
    result = analogical.find_analogies(current_situation_desc)
    
    assert len(result) == 0

def test_find_analogies_empty_current_situation_desc(analogical, mock_kb):
    analogical.knowledge_base = mock_kb
    current_situation_desc = ""
    
    result = analogical.find_analogies(current_situation_desc)
    
    assert len(result) == 0

def test_find_analogies_invalid_domain(analogical, mock_kb):
    analogical.knowledge_base = mock_kb
    current_situation_desc = "Refactor the codebase"
    
    result = analogical.find_analogies(current_situation_desc, target_domain="Non-Existent")
    
    assert len(result) == 0

def test_find_analogies_no_matching_analogies(analogical):
    analogical.knowledge_base = [
        MockKBItem("Software Engineering", {"A": "C"}, "Refactor"),
        MockKBItem("Manufacturing", {"X": "Z"}, "Reorganize")
    ]
    current_situation_desc = "Refactor the codebase"
    
    result = analogical.find_analogies(current_situation_desc)
    
    assert len(result) == 0

def test_find_analogies_low_similarity_threshold(analogical, mock_kb):
    analogical.knowledge_base = mock_kb
    current_situation_desc = "Refactor the codebase"
    analogical._structural_similarity.return_value = 0.05
    
    result = analogical.find_analogies(current_situation_desc)
    
    assert len(result) == 0

def test_find_analogies_single_match(analogical, mock_kb):
    analogical.knowledge_base = [
        MockKBItem("Software Engineering", {"A": "B"}, "Refactor")
    ]
    current_situation_desc = "Refactor the codebase"
    
    result = analogical.find_analogies(current_situation_desc)
    
    assert len(result) == 1
    match = result[0]
    assert isinstance(match, AnalogyMatch)

def test_find_analogies_multiple_matches(analogical, mock_kb):
    analogical.knowledge_base = [
        MockKBItem("Software Engineering", {"A": "B"}, "Refactor"),
        MockKBItem("Manufacturing", {"X": "Y"}, "Reorganize")
    ]
    current_situation_desc = "Refactor the codebase"
    
    result = analogical.find_analogies(current_situation_desc)
    
    assert len(result) == 2
    for match in result:
        assert isinstance(match, AnalogyMatch)