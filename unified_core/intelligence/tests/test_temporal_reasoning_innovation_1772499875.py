import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from sqlalchemy.engine import create_engine

class MockEngine:
    def execute(self, query):
        return pd.DataFrame({
            'timestamp': [pd.Timestamp('2023-01-01 00:00:00')],
            'value': [1]
        })

@pytest.fixture
def temporal_reasoning():
    engine = MockEngine()
    with patch('unified_core.intelligence.temporal_reasoning.create_engine', return_value=engine):
        from unified_core.intelligence import TemporalReasoning
        return TemporalReasoning()

def test_load_history_happy_path(temporal_reasoning):
    df = temporal_reasoning.load_history('test_table')
    assert not df.empty
    assert 'timestamp' in df.columns
    assert 'value' in df.columns

def test_load_history_edge_case_empty_table(temporal_reasoning):
    engine = MockEngine()
    def mock_execute(query):
        return pd.DataFrame(columns=['timestamp', 'value'])
    with patch.object(engine, 'execute', mock_execute):
        df = temporal_reasoning.load_history('test_table')
        assert df.empty

def test_load_history_edge_case_none_time_window(temporal_reasoning):
    with pytest.raises(ValueError) as exc_info:
        temporal_reasoning.load_history('test_table', time_window=None)
    assert "time_window cannot be None" == str(exc_info.value)

def test_load_history_error_case_invalid_time_window(temporal_reasoning):
    with pytest.raises(ValueError) as exc_info:
        temporal_reasoning.load_history('test_table', time_window='invalid')
    assert "Invalid time window format" == str(exc_info.value)