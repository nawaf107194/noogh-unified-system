import pytest

class TradingFeature:
    def __init__(self):
        self.support_levels = [10, 20, 30]
        self.resistance_levels = [40, 50, 60]

    def get_levels(self):
        """
        Returns the detected support and resistance levels.
        """
        return {
            'support': self.support_levels,
            'resistance': self.resistance_levels
        }

@pytest.fixture
def trading_feature():
    return TradingFeature()

def test_get_levels_happy_path(trading_feature):
    result = trading_feature.get_levels()
    assert isinstance(result, dict)
    assert 'support' in result and isinstance(result['support'], list)
    assert 'resistance' in result and isinstance(result['resistance'], list)

def test_get_levels_empty(trading_feature):
    trading_feature.support_levels = []
    trading_feature.resistance_levels = []
    result = trading_feature.get_levels()
    assert isinstance(result, dict)
    assert 'support' in result and isinstance(result['support'], list) and not result['support']
    assert 'resistance' in result and isinstance(result['resistance'], list) and not result['resistance']

def test_get_levels_none(trading_feature):
    trading_feature.support_levels = None
    trading_feature.resistance_levels = None
    result = trading_feature.get_levels()
    assert isinstance(result, dict)
    assert 'support' in result and isinstance(result['support'], list) and not result['support']
    assert 'resistance' in result and isinstance(result['resistance'], list) and not result['resistance']

def test_get_levels_boundary(trading_feature):
    trading_feature.support_levels = [10]
    trading_feature.resistance_levels = [60]
    result = trading_feature.get_levels()
    assert isinstance(result, dict)
    assert 'support' in result and isinstance(result['support'], list) and len(result['support']) == 1
    assert 'resistance' in result and isinstance(result['resistance'], list) and len(result['resistance']) == 1

def test_get_levels_no_support(trading_feature):
    trading_feature.support_levels = None
    trading_feature.resistance_levels = [40, 50, 60]
    result = trading_feature.get_levels()
    assert isinstance(result, dict)
    assert 'support' in result and isinstance(result['support'], list) and not result['support']
    assert 'resistance' in result and isinstance(result['resistance'], list)

def test_get_levels_no_resistance(trading_feature):
    trading_feature.support_levels = [10, 20, 30]
    trading_feature.resistance_levels = None
    result = trading_feature.get_levels()
    assert isinstance(result, dict)
    assert 'support' in result and isinstance(result['support'], list)
    assert 'resistance' in result and isinstance(result['resistance'], list) and not result['resistance']