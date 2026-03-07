import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

class MockFuturesClient:
    def open_position(self, *args, **kwargs):
        return {'success': True, 'message': 'Trade executed'}

class TestAdvancedStrategy:
    @pytest.fixture
    def strategy():
        from trading.advanced_strategy import AdvancedStrategy
        strategy = AdvancedStrategy(read_only=False)
        strategy.futures = MockFuturesClient()
        strategy.tracker = MagicMock()
        return strategy

    def test_happy_path(self, strategy):
        analysis = {
            'signal': 'LONG',
            'symbol': 'BTCUSDT',
            'quantity': 0.01,
            'stop_loss': 3000,
            'entry_price': 3500,
            'take_profit': 4000,
            'reasons': ['RSI overbought'],
            'liquidity_score': 80,
            'strength': 'Strong'
        }
        result = strategy.execute_trade(analysis)
        assert result['success'] is True
        assert result['message'] == "✅ Trade executed: LONG BTCUSDT"
        assert isinstance(result['trade'], Trade)
        assert strategy.tracker.add_trade.call_count == 1

    def test_read_only_mode(self, strategy):
        strategy.read_only = True
        analysis = {
            'signal': 'LONG',
            'symbol': 'BTCUSDT',
            'quantity': 0.01,
            'stop_loss': 3000,
            'entry_price': 3500,
            'take_profit': 4000,
            'reasons': ['RSI overbought'],
            'liquidity_score': 80,
            'strength': 'Strong'
        }
        result = strategy.execute_trade(analysis)
        assert result['success'] is False
        assert result['message'] == '🔒 Read-only mode - Trade simulation only'

    def test_no_signal(self, strategy):
        analysis = {
            'signal': None,
            'symbol': 'BTCUSDT',
            'quantity': 0.01,
            'stop_loss': 3000,
            'entry_price': 3500,
            'take_profit': 4000,
            'reasons': ['RSI overbought'],
            'liquidity_score': 80,
            'strength': 'Strong'
        }
        result = strategy.execute_trade(analysis)
        assert result['success'] is False
        assert result['message'] == 'No signal'

    def test_invalid_symbol(self, strategy):
        analysis = {
            'signal': 'LONG',
            'symbol': 'INVALID_SYMBOL',
            'quantity': 0.01,
            'stop_loss': 3000,
            'entry_price': 3500,
            'take_profit': 4000,
            'reasons': ['RSI overbought'],
            'liquidity_score': 80,
            'strength': 'Strong'
        }
        result = strategy.execute_trade(analysis)
        assert result['success'] is False
        assert 'Execution failed' in result['message']

    def test_exception(self, strategy):
        with patch.object(strategy.futures, 'open_position', side_effect=Exception('Simulated exception')):
            analysis = {
                'signal': 'LONG',
                'symbol': 'BTCUSDT',
                'quantity': 0.01,
                'stop_loss': 3000,
                'entry_price': 3500,
                'take_profit': 4000,
                'reasons': ['RSI overbought'],
                'liquidity_score': 80,
                'strength': 'Strong'
            }
            result = strategy.execute_trade(analysis)
            assert result['success'] is False
            assert 'Execution error' in result['message']