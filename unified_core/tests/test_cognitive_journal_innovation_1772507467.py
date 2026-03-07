import pytest

from unified_core.cognitive_journal import get_cognitive_journal, CognitiveJournal

@pytest.fixture
def mock_journal():
    """Mock a CognitiveJournal instance."""
    class MockCognitiveJournal(CognitiveJournal):
        pass
    return MockCognitiveJournal()

def test_get_cognitive_journal_happy_path(monkeypatch, mock_journal):
    """Test the happy path when the journal already exists."""
    monkeypatch.setattr(unified_core.cognitive_journal, "_journal_instance", mock_journal)
    result = get_cognitive_journal()
    assert result is mock_journal

def test_get_cognitive_journal_create_new():
    """Test that a new journal instance is created if it does not exist."""
    global _journal_instance
    _journal_instance = None
    result = get_cognitive_journal()
    assert isinstance(result, CognitiveJournal)
    assert result is _journal_instance