import pytest

class MockLibrary:
    def _print_import_summary(self, imported: List[Dict], skipped: List[str]):
        """Print a nice summary to console."""
        print(f"\n{'='*70}")
        print("📊 Import Complete:")
        print(f"  ✅ Imported: {len(imported)}")
        print(f"  ⚠️  Skipped: {len(skipped)}")
        if imported:
            avg_q = sum(p["quality"] for p in imported) / len(imported)
            print(f"  📈 Avg Quality: {avg_q:.2f}")
        print(f"{'='*70}")

@pytest.fixture
def mock_library():
    return MockLibrary()

def test_print_import_summary_happy_path(mock_library, capsys):
    """Test happy path with normal inputs."""
    imported = [
        {"name": "module1", "quality": 95},
        {"name": "module2", "quality": 85}
    ]
    skipped = ["module3"]
    mock_library._print_import_summary(imported, skipped)
    captured = capsys.readouterr()
    assert captured.out == """
====================================================================================================
📊 Import Complete:
  ✅ Imported: 2
  ⚠️  Skipped: 1
  📈 Avg Quality: 90.00
====================================================================================================
"""

def test_print_import_summary_empty_lists(mock_library, capsys):
    """Test with empty lists."""
    imported = []
    skipped = []
    mock_library._print_import_summary(imported, skipped)
    captured = capsys.readouterr()
    assert captured.out == """
====================================================================================================
📊 Import Complete:
  ✅ Imported: 0
  ⚠️  Skipped: 0
====================================================================================================
"""

def test_print_import_summary_no_imports(mock_library, capsys):
    """Test with no imports."""
    imported = []
    skipped = ["module1", "module2"]
    mock_library._print_import_summary(imported, skipped)
    captured = capsys.readouterr()
    assert captured.out == """
====================================================================================================
📊 Import Complete:
  ✅ Imported: 0
  ⚠️  Skipped: 2
====================================================================================================
"""

def test_print_import_summary_invalid_input(mock_library):
    """Test with invalid input types."""
    with pytest.raises(ValueError) as exc_info:
        mock_library._print_import_summary({"invalid": "input"}, ["module1"])
    assert str(exc_info.value) == "Invalid input type for 'imported'. Expected List[Dict], got Dict"