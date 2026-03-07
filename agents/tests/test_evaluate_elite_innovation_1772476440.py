import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json

class MockAgent:
    def __init__(self, data_file):
        self.data_file = Path(data_file)

def test_load_historical_data_happy_path(tmpdir):
    agent = MockAgent(str(tmpdir / 'historical_data.json'))
    (tmpdir / 'historical_data.json').write_text(json.dumps([
        {'timestamp': '2023-01-01', 'data': 'A'},
        {'timestamp': '2023-01-02', 'data': 'B'}
    ]))

    setups = agent.load_historical_data()
    assert len(setups) == 2
    assert setups[0]['timestamp'] == '2023-01-01'
    assert setups[1]['timestamp'] == '2023-01-02'

def test_load_historical_data_empty_file(tmpdir):
    agent = MockAgent(str(tmpdir / 'historical_data.json'))
    (tmpdir / 'historical_data.json').write_text('')

    setups = agent.load_historical_data()
    assert len(setups) == 0

def test_load_historical_data_nonexistent_file():
    agent = MockAgent('/path/to/nonexistent/file')
    setups = agent.load_historical_data()
    assert setups is None

@patch('builtins.json.loads')
def test_load_historical_data_invalid_json(mock_loads):
    agent = MockAgent(str(tmpdir / 'historical_data.json'))
    (tmpdir / 'historical_data.json').write_text('"invalid json"')

    with pytest.raises(json.JSONDecodeError):
        agent.load_historical_data()