import pytest
from unittest.mock import patch
from unified_core.cognitive_journal import CognitiveJournal, get_cognitive_journal

@pytest.fixture
def reset_journal():
    """Fixture to reset the journal instance before each test"""
    from unified_core.cognitive_journal import _journal_instance
    _journal_instance = None
    yield

def test_get_cognitive_journal_happy_path(reset_journal):
    """Test that the function returns the same journal instance on consecutive calls"""
    journal1 = get_cognitive_journal()
    journal2 = get_cognitive_journal()
    assert journal1 is journal2, "Should return the same instance on consecutive calls"
    assert isinstance(journal1, CognitiveJournal), "Should return a CognitiveJournal instance"

def test_get_cognitive_journal_initialization(reset_journal):
    """Test that the journal is properly initialized when first accessed"""
    journal = get_cognitive_journal()
    assert journal is not None, "Journal instance should not be None"
    assert hasattr(journal, 'entries'), "Journal should have entries attribute"
    assert len(journal.entries) == 0, "New journal should start with empty entries"

def test_get_cognitive_journal_after_reset(reset_journal):
    """Test that the journal instance is recreated after being reset"""
    journal1 = get_cognitive_journal()
    reset_journal()  # Manually reset the journal
    journal2 = get_cognitive_journal()
    assert journal1 is not journal2, "Should create a new instance after reset"
    assert isinstance(journal2, CognitiveJournal), "Should return a CognitiveJournal instance"