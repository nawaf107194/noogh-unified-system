import pytest
from gateway.app.analytics.kpi_calculator import KPICalculator

class MockKPIs:
    @staticmethod
    def _get_events_in_window(window_seconds):
        # Return a list of mock events with received_at timestamps
        return [
            {'received_at': 1640966400},  # 2022-01-01 00:00:00
            {'received_at': 1640970000},  # 2022-01-01 01:00:00
            {'received_at': 1640973600},  # 2022-01-01 02:00:00
        ]

    @staticmethod
    def _calc_approval_rate(bucket_events):
        return len(bucket_events) / len(bucket_events)

    @staticmethod
    def _calc_success_rate(bucket_events):
        return sum(1 for e in bucket_events if e.get('success', False)) / len(bucket_events)

    @staticmethod
    def _calc_avg_confidence(bucket_events):
        return sum(e.get('confidence', 0) for e in bucket_events) / len(bucket_events)

# Monkey patch the KPIs class with mock methods
class MockKPIsCalculator(KPICalculator):
    _get_events_in_window = MockKPIs._get_events_in_window
    _calc_approval_rate = MockKPIs._calc_approval_rate
    _calc_success_rate = MockKPIs._calc_success_rate
    _calc_avg_confidence = MockKPIs._calc_avg_confidence

def test_get_trends_happy_path():
    calculator = MockKPIsCalculator()
    result = calculator.get_trends(window_seconds=3600, buckets=1)
    assert 'timestamps' in result
    assert len(result['timestamps']) == 1
    assert 'trends' in result
    assert 'approval_rate' in result['trends']
    assert 'success_rate' in result['trends']
    assert 'avg_confidence' in result['trends']
    assert 'buckets' in result

def test_get_trends_empty_events():
    calculator = MockKPIsCalculator()
    calculator._get_events_in_window = lambda window_seconds: []
    result = calculator.get_trends(window_seconds=86400, buckets=24)
    assert result == {'buckets': [], 'trends': {}}

def test_get_trends_invalid_inputs():
    calculator = MockKPIsCalculator()
    with pytest.raises(ValueError):
        calculator.get_trends(window_seconds=-1, buckets=24)
    with pytest.raises(ValueError):
        calculator.get_trends(window_seconds=86400, buckets=-1)

# Async behavior is not applicable in this synchronous code