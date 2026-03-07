import pytest

class MockLiveTrader:
    def __init__(self, testnet=False, mode='paper', read_only=False, positions=None):
        self.testnet = testnet
        self.mode = mode
        self.read_only = read_only
        self.positions = positions if positions else {}

    @property
    def positions(self):
        return self._positions

    @positions.setter
    def positions(self, value):
        self._positions = {symbol: Position(**pos) for symbol, pos in value.items()}

class Position:
    def __init__(self, side='long', entry_price=100, quick_tp_hit=False, trailing_stop=None, qty_quick=0, qty_trail=0):
        self.side = side
        self.entry_price = entry_price
        self.quick_tp_hit = quick_tp_hit
        self.trailing_stop = trailing_stop
        self.qty_quick = qty_quick
        self.qty_trail = qty_trail

    @property
    def qty_remaining(self):
        return self.qty_quick + self.qty_trail

def test_get_status_happy_path():
    trader = MockLiveTrader(
        testnet=False,
        mode='paper',
        read_only=True,
        positions={
            'BTC/USD': {
                'side': 'long',
                'entry_price': 100,
                'quick_tp_hit': False,
                'trailing_stop': None,
                'qty_quick': 1,
                'qty_trail': 2
            },
            'ETH/USD': {
                'side': 'short',
                'entry_price': 200,
                'quick_tp_hit': True,
                'trailing_stop': 190,
                'qty_quick': 3,
                'qty_trail': 4
            }
        }
    )
    expected_status = {
        'network': 'PRODUCTION',
        'mode': 'paper',
        'paper_trade': True,
        'active_positions': 2,
        'positions': {
            'BTC/USD': {
                'side': 'long',
                'entry': 100,
                'quick_tp_hit': False,
                'trailing_stop': None,
                'qty_remaining': 3
            },
            'ETH/USD': {
                'side': 'short',
                'entry': 200,
                'quick_tp_hit': True,
                'trailing_stop': 190,
                'qty_remaining': 7
            }
        }
    }
    assert trader.get_status() == expected_status

def test_get_status_empty_positions():
    trader = MockLiveTrader(
        testnet=True,
        mode='live',
        read_only=False,
        positions={}
    )
    expected_status = {
        'network': 'TESTNET',
        'mode': 'live',
        'paper_trade': False,
        'active_positions': 0,
        'positions': {}
    }
    assert trader.get_status() == expected_status

def test_get_status_read_only_mode():
    trader = MockLiveTrader(
        testnet=False,
        mode='paper',
        read_only=True,
        positions={
            'BTC/USD': {
                'side': 'long',
                'entry_price': 100,
                'quick_tp_hit': False,
                'trailing_stop': None,
                'qty_quick': 1,
                'qty_trail': 2
            }
        }
    )
    expected_status = {
        'network': 'PRODUCTION',
        'mode': 'paper',
        'paper_trade': True,
        'active_positions': 1,
        'positions': {
            'BTC/USD': {
                'side': 'long',
                'entry': 100,
                'quick_tp_hit': False,
                'trailing_stop': None,
                'qty_remaining': 3
            }
        }
    }
    assert trader.get_status() == expected_status

def test_get_status_async_behavior():
    # This is not applicable as the function is synchronous
    pass