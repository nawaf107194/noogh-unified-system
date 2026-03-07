import pytest

class TestDataCompaction:
    def setup_method(self):
        self.test_cases = [
            ("path/to/ledger", "path/to/beliefs"),
            ("", ""),
            (None, None),
            ("path/to/ledger", None),
            (None, "path/to/beliefs"),
            ("path/to/ledger", "", 0),
            ("", "path/to/beliefs", 0),
            (None, None, -1)
        ]

    @pytest.mark.parametrize("ledger_path,beliefs_path,retention_days", test_cases)
    def test_init(self, ledger_path, beliefs_path, retention_days):
        data_compaction = DataCompaction(ledger_path, beliefs_path, retention_days)
        assert data_compaction.ledger_path == ledger_path
        assert data_compaction.beliefs_path == beliefs_path
        assert data_compaction.retention_days == retention_days

    def test_init_with_invalid_retention_days(self):
        with pytest.raises(ValueError) as exc_info:
            DataCompaction("path/to/ledger", "path/to/beliefs", -1)
        assert str(exc_info.value) == "Retention days must be a positive integer."

    def test_async_behavior(self, event_loop):
        async def create_data_compaction():
            return DataCompaction("path/to/ledger", "path/to/beliefs")

        data_compaction = event_loop.run_until_complete(create_data_compaction())
        assert isinstance(data_compaction, DataCompaction)
        assert data_compaction.ledger_path == "path/to/ledger"
        assert data_compaction.beliefs_path == "path/to/beliefs"
        assert data_compaction.retention_days == 30