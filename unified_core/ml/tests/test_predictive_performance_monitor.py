import pytest
from unittest.mock import patch, Mock
from typing import List

from unified_core.ml.predictive_performance_monitor import PredictivePerformanceMonitor, PredictiveAlert

class TestPredictivePerformanceMonitor:

    @pytest.fixture
    def monitor(self):
        return PredictivePerformanceMonitor()

    @patch.object(PredictivePerformanceMonitor, 'predict_future_metrics', return_value={'metric': 10})
    @patch.object(PredictivePerformanceMonitor, 'analyze_predictions', return_value=[PredictiveAlert()])
    def test_happy_path(self, mock_analyze, mock_predict, monitor):
        # Mock the current time to avoid time-based checks
        with patch('time.time', return_value=0):
            alerts = monitor.check_and_alert()
        assert len(alerts) == 1
        assert isinstance(alerts[0], PredictiveAlert)
        mock_predict.assert_called_once()
        mock_analyze.assert_called_once()

    @patch.object(PredictivePerformanceMonitor, 'predict_future_metrics', return_value=None)
    def test_no_predictions(self, mock_predict, monitor):
        with patch('time.time', return_value=0):
            alerts = monitor.check_and_alert()
        assert not alerts
        mock_predict.assert_called_once()

    @patch.object(PredictivePerformanceMonitor, 'analyze_predictions', return_value=[PredictiveAlert()])
    def test_rate_limit(self, mock_analyze, monitor):
        # Mock the current time to simulate a recent prediction
        with patch('time.time', side_effect=[0, 1]):
            alerts = monitor.check_and_alert()
            assert not alerts
            alerts = monitor.check_and_alert()
            assert len(alerts) == 1

    @patch.object(PredictivePerformanceMonitor, 'predict_future_metrics')
    def test_analyze_predictions_error(self, mock_predict, monitor):
        # Simulate an error in analyze_predictions
        mock_predict.return_value = {'metric': 10}
        mock_analyze.return_value = None

        with patch('time.time', return_value=0):
            alerts = monitor.check_and_alert()
        assert not alerts

    @patch.object(PredictivePerformanceMonitor, 'predict_future_metrics')
    def test_invalid_inputs(self, mock_predict, monitor):
        # Simulate invalid inputs that should not cause an error
        mock_predict.return_value = {'invalid_key': 'value'}

        with patch('time.time', return_value=0):
            alerts = monitor.check_and_alert()
        assert not alerts