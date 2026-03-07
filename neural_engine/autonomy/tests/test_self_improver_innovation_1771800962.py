import pytest
from neural_engine.autonomy.self_improver import SelfImprover, FileCategory

@pytest.fixture
def self_improver():
    return SelfImprover()

@pytest.fixture
def dummy_diagnosis():
    return {
        "category": 1,
        "health_score": 85,
        "issues": ["PEP8 violations", "Unused imports"]
    }

def test_analyze_for_improvements_happy_path(self_improver, dummy_diagnosis):
    category = FileCategory(1)
    self_improver.IMPROVABLE_CATEGORIES = {category}
    self_improver.JUSTIFICATION_REQUIRED = set()
    self_improver.PROTECTED_CATEGORIES = set()
    
    with patch.object(SelfImprover, 'doctor', return_value=dummy_diagnosis):
        result = self_improver.analyze_for_improvements("test_file.py")
    
    assert result == {
        "filepath": "test_file.py",
        "category": category.value,
        "health_score": 85,
        "issues": ["PEP8 violations", "Unused imports"],
        "can_propose_improvements": True,
        "needs_justification": False,
        "is_protected": False,
        "potential_improvements": self_improver._identify_improvements(dummy_diagnosis),
        "guidance": self_improver._get_improvement_guidance(category)
    }

def test_analyze_for_improvements_category_can_propose(self_improver, dummy_diagnosis):
    category = FileCategory(1)
    self_improver.IMPROVABLE_CATEGORIES = {category}
    self_improver.JUSTIFICATION_REQUIRED = set()
    self_improver.PROTECTED_CATEGORIES = set()
    
    with patch.object(SelfImprover, 'doctor', return_value=dummy_diagnosis):
        result = self_improver.analyze_for_improvements("test_file.py")
    
    assert result["can_propose_improvements"] is True
    assert result["potential_improvements"] == self_improver._identify_improvements(dummy_diagnosis)

def test_analyze_for_improvements_category_needs_justification(self_improver, dummy_diagnosis):
    category = FileCategory(2)
    self_improver.IMPROVABLE_CATEGORIES = set()
    self.improver.JUSTIFICATION_REQUIRED = {category}
    self.improver.PROTECTED_CATEGORIES = set()
    
    with patch.object(SelfImprover, 'doctor', return_value=dummy_diagnosis):
        result = self_improver.analyze_for_improvements("test_file.py")
    
    assert result["needs_justification"] is True
    assert result["potential_improvements"] == []

def test_analyze_for_improvements_category_protected(self_improver, dummy_diagnosis):
    category = FileCategory(3)
    self_improver.IMPROVABLE_CATEGORIES = set()
    self.improver.JUSTIFICATION_REQUIRED = set()
    self.improver.PROTECTED_CATEGORIES = {category}
    
    with patch.object(SelfImprover, 'doctor', return_value=dummy_diagnosis):
        result = self_improver.analyze_for_improvements("test_file.py")
    
    assert result["is_protected"] is True
    assert result["potential_improvements"] == []
    assert result["protection_reason"] == self_improver._get_protection_reason(category)

def test_analyze_for_improvements_empty_filepath(self_improver):
    with pytest.raises(ValueError, match="Invalid filepath: None"):
        self_improver.analyze_for_improvements(None)

def test_analyze_for_improvements_nonexistent_filepath(self_improver):
    with pytest.raises(FileNotFoundError, match="File not found: 'nonexistent_file.py'"):
        self_improver.analyze_for_improvements("nonexistent_file.py")