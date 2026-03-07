import pytest

from unified_core.cognitive_journal import CognitiveJournal, Entry

class TestCognitiveJournal:

    @pytest.fixture
    def journal(self):
        return CognitiveJournal()

    def test_happy_path(self, journal):
        # Arrange
        entries = [
            Entry(entry_type="success", content="Test success"),
            Entry(entry_type="discovery", content="Test discovery"),
            Entry(entry_type="failure", content="Test failure")
        ]
        journal._entries = entries

        # Act
        result = journal.get_evolution_context()

        # Assert
        expected_result = """# السجل المعرفي الأخير
- ✅ [success] Test success
  → None: None
- 💡 [discovery] Test discovery
  → None: None
- ❌ [failure] Test failure
  → None: None"""
        assert result == expected_result

    def test_empty_entries(self, journal):
        # Arrange
        journal._entries = []

        # Act
        result = journal.get_evolution_context()

        # Assert
        expected_result = "لا يوجد سجل معرفي سابق. هذه أول دورة."
        assert result == expected_result

    def test_none_entries(self, journal):
        # Arrange
        journal._entries = None

        # Act
        result = journal.get_evolution_context()

        # Assert
        expected_result = "لا يوجد سجل معرفي سابق. هذه أول دورة."
        assert result == expected_result

    def test_boundary_max_entries(self, journal):
        # Arrange
        entries = [Entry(entry_type="decision", content="Test decision") for _ in range(10)]
        journal._entries = entries

        # Act
        result_with_max = journal.get_evolution_context(max_entries=5)
        result_without_max = journal.get_evolution_context()

        # Assert
        expected_result_with_max = """# السجل المعرفي الأخير
- 🎯 [decision] Test decision
  → None: None
- 🎯 [decision] Test decision
  → None: None
- 🎯 [decision] Test decision
  → None: None
- 🎯 [decision] Test decision
  → None: None
- 🎯 [decision] Test decision
  → None: None"""
        assert result_with_max == expected_result_with_max

        expected_result_without_max = """# السجل المعرفي الأخير
- 🎯 [decision] Test decision
  → None: None
- 🎯 [decision] Test decision
  → None: None
- 🎯 [decision] Test decision
  → None: None
- 🎯 [decision] Test decision
  → None: None
- 🎯 [decision] Test decision
  → None: None
- 🎯 [decision] Test decision
  → None: None
- 🎯 [decision] Test decision
  → None: None
- 🎯 [decision] Test decision
  → None: None
- 🎯 [decision] Test decision
  → None: None"""
        assert result_without_max == expected_result_without_max

    def test_invalid_input_type(self, journal):
        # Arrange
        with pytest.raises(TypeError):
            journal.get_evolution_context(max_entries="not an int")