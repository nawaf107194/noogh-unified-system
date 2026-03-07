import pytest
from unittest.mock import patch, MagicMock

from agents.evaluate_elite import EvaluateElite

class TestEvaluateWindows:

    @pytest.fixture
    def evaluate_elite_instance(self):
        return EvaluateElite()

    @pytest.fixture
    def mock_load_historical_data(self, monkeypatch):
        setups = [
            {'id': 1, 'data': [10, 20, 30]},
            {'id': 2, 'data': [40, 50, 60]},
            {'id': 3, 'data': [70, 80, 90]}
        ]
        monkeypatch.setattr(EvaluateElite, "load_historical_data", MagicMock(return_value=setups))

    @pytest.fixture
    def mock_evaluate_layer_c(self, monkeypatch):
        mock = MagicMock()
        mock.return_value = {
            'total_setups': 3,
            'layer_b_passed': 2,
            'layer_c_passed': 1,
            'layer_c_rejected': 0,
            'trades': 2,
            'wins': 1,
            'losses': 1,
            'winrate': 50.0,
            'total_r': 2.0,
            'pf': 2.0,
            'avg_win_r': 1.0,
            'avg_loss_r': -1.0,
            'max_dd_r': 0.0,
            'final_equity': 3.0
        }
        monkeypatch.setattr(EvaluateElite, "evaluate_layer_c", mock)
        return mock

    def test_happy_path(self, evaluate_elite_instance, mock_load_historical_data, mock_evaluate_layer_c):
        result = evaluate_elite_instance.evaluate_windows("long_func", "short_func")
        assert len(result) == 3
        for window_name in ["A", "B", "ALL"]:
            assert window_name in result
            assert 'total_setups' in result[window_name]
            assert 'layer_b_passed' in result[window_name]
            assert 'layer_c_passed' in result[window_name]

    def test_empty_data(self, evaluate_elite_instance):
        mock_load_historical_data = MagicMock(return_value=[])
        with patch.object(evaluate_elite_instance, "load_historical_data", mock_load_historical_data):
            result = evaluate_elite_instance.evaluate_windows("long_func", "short_func")
            assert not result
            assert mock_load_historical_data.called

    def test_none_data(self, evaluate_elite_instance):
        mock_load_historical_data = MagicMock(return_value=None)
        with patch.object(evaluate_elite_instance, "load_historical_data", mock_load_historical_data):
            result = evaluate_elite_instance.evaluate_windows("long_func", "short_func")
            assert not result
            assert mock_load_historical_data.called

    def test_eval_mode_invalid(self, evaluate_elite_instance):
        mock_evaluate_layer_c = MagicMock()
        with patch.object(evaluate_elite_instance, "evaluate_layer_c", mock_evaluate_layer_c):
            with pytest.raises(ValueError) as exc_info:
                evaluate_elite_instance.evaluate_windows("long_func", "short_func", eval_mode="INVALID")
            assert str(exc_info.value) == "Invalid eval mode: INVALID"

    def test_async_behavior(self, evaluate_elite_instance, mock_load_historical_data, mock_evaluate_layer_c):
        asyncio = MagicMock()
        asyncio.sleep.return_value = None
        with patch('asyncio', asyncio):
            evaluate_elite_instance.evaluate_windows("long_func", "short_func")
            assert asyncio.sleep.called_once_with(0)