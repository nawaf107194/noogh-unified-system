import pytest

class ContinuousTrainingLoop:
    def calculate_performance(self, setups):
        long_wins = len([s for s in setups if s['signal'] == 'LONG' and s.get('outcome') == 'WIN'])
        long_losses = len([s for s in setups if s['signal'] == 'LONG' and s.get('outcome') == 'LOSS'])
        short_wins = len([s for s in setups if s['signal'] == 'SHORT' and s.get('outcome') == 'WIN'])
        short_losses = len([s for s in setups if s['signal'] == 'SHORT' and s.get('outcome') == 'LOSS'])

        return {
            'total_setups': len(setups),
            'long': {'wins': long_wins, 'losses': long_losses},
            'short': {'wins': short_wins, 'losses': short_losses}
        }

@pytest.fixture
def calculator():
    return ContinuousTrainingLoop()

# Happy path (normal inputs)
def test_calculate_performance_happy_path(calculator):
    setups = [
        {'signal': 'LONG', 'outcome': 'WIN'},
        {'signal': 'LONG', 'outcome': 'LOSS'},
        {'signal': 'SHORT', 'outcome': 'WIN'},
        {'signal': 'SHORT', 'outcome': 'WIN'}
    ]
    result = calculator.calculate_performance(setups)
    assert result == {
        'total_setups': 4,
        'long': {'wins': 1, 'losses': 1},
        'short': {'wins': 2, 'losses': 0}
    }

# Edge cases (empty, None, boundaries)
def test_calculate_performance_empty_input(calculator):
    setups = []
    result = calculator.calculate_performance(setups)
    assert result == {
        'total_setups': 0,
        'long': {'wins': 0, 'losses': 0},
        'short': {'wins': 0, 'losses': 0}
    }

def test_calculate_performance_none_input(calculator):
    setups = None
    result = calculator.calculate_performance(setups)
    assert result is None

# Error cases (invalid inputs) ONLY IF the code explicitly raises them
# The provided function does not raise any specific exceptions, so no need to test error cases for now.

# Async behavior (if applicable)
# The provided function is synchronous and does not involve async behavior, so no need to test it.