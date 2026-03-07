import pytest
from pathlib import Path
from typing import List, Dict

class SelfAnalysis:
    pass

class ImprovementProposal:
    pass

class Any:
    pass

class SelfGoverner:
    def __init__(self, data_dir: str = "data/self_improvement"):
        """Initialize self-governing agent."""
        self.data_dir = Path(data_dir)
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True, exist_ok=True)

        self.analysis_history: List[SelfAnalysis] = []
        self.proposals: Dict[str, ImprovementProposal] = {}
        self.learned_patterns: Dict[str, Any] = {}
        self.performance_log: List[Dict] = []

        self._load_state()

def test_init_happy_path():
    # Test with normal inputs
    sg = SelfGoverner("data/test_dir")
    assert isinstance(sg.data_dir, Path)
    assert sg.data_dir.exists()
    assert isinstance(sg.analysis_history, list)
    assert isinstance(sg.proposals, dict)
    assert isinstance(sg.learned_patterns, dict)
    assert isinstance(sg.performance_log, list)

def test_init_edge_case_empty_str():
    # Test with empty string
    sg = SelfGoverner("")
    assert isinstance(sg.data_dir, Path)
    assert sg.data_dir.exists()
    assert isinstance(sg.analysis_history, list)
    assert isinstance(sg.proposals, dict)
    assert isinstance(sg.learned_patterns, dict)
    assert isinstance(sg.performance_log, list)

def test_init_edge_case_none():
    # Test with None
    with pytest.raises(TypeError):
        sg = SelfGoverner(None)

def test_init_error_case_invalid_path():
    # Test with invalid path
    with pytest.raises(FileNotFoundError):
        sg = SelfGoverner("/nonexistent/path")