import pytest

class TestDataCompactionInit:

    def test_happy_path(self):
        # Normal inputs
        dc = DataCompaction("path/to/ledger", "path/to/beliefs")
        assert dc.ledger_path == "path/to/ledger"
        assert dc.beliefs_path == "path/to/beliefs"
        assert dc.retention_days == 30

    def test_edge_case_empty_strings(self):
        # Edge case: empty strings
        with pytest.raises(ValueError, match="Paths cannot be empty"):
            DataCompaction("", "")

    def test_edge_case_none_values(self):
        # Edge case: None values
        with pytest.raises(ValueError, match="Paths cannot be None"):
            DataCompaction(None, None)

    def test_error_case_invalid_retention_days(self):
        # Error case: invalid retention days (non-integer)
        with pytest.raises(TypeError, match="retention_days must be an integer"):
            DataCompaction("path/to/ledger", "path/to/beliefs", retention_days="30")

        with pytest.raises(ValueError, match="retention_days must be a positive integer"):
            DataCompaction("path/to/ledger", "path/to/beliefs", retention_days=-1)

    def test_async_behavior(self):
        # Async behavior (if applicable)
        # Assuming the __init__ method does not perform async operations
        pass  # No async behavior to test for this __init__

# Run these tests using pytest in your terminal:
# pytest /path/to/test_data_compaction_init.py