import pytest
from pathlib import Path
from agents.funding_monitor_daemon import FundingMonitorDaemon, FundingRegimeDetector

@pytest.fixture
def fmd():
    return FundingMonitorDaemon()

def test_init_happy_path(fmd):
    assert isinstance(fmd.detector, FundingRegimeDetector)
    assert fmd.alert_threshold_hot == 0.0010
    assert fmd.alert_threshold_warm == 0.0004
    assert fmd.last_scan is None
    assert fmd.previous_regimes == {}
    assert fmd.alerts_file == Path(__file__).parent.parent / 'data' / 'funding_alerts.jsonl'

def test_init_default_thresholds(fmd):
    detector = FundingMonitorDaemon(alert_threshold_hot=None, alert_threshold_warm=None)
    assert isinstance(detector.detector, FundingRegimeDetector)
    assert detector.alert_threshold_hot == 0.0010
    assert detector.alert_threshold_warm == 0.0004

def test_init_custom_thresholds():
    detector = FundingMonitorDaemon(alert_threshold_hot=0.01, alert_threshold_warm=0.005)
    assert isinstance(detector.detector, FundingRegimeDetector)
    assert detector.alert_threshold_hot == 0.01
    assert detector.alert_threshold_warm == 0.005

def test_init_non_numeric_thresholds():
    with pytest.raises(TypeError):
        FundingMonitorDaemon(alert_threshold_hot="0.001", alert_threshold_warm="0.0004")

def test_init_invalid_thresholds():
    with pytest.raises(ValueError):
        FundingMonitorDaemon(alert_threshold_hot=0.0, alert_threshold_warm=0.0)

def test_init_boundary_thresholds():
    detector = FundingMonitorDaemon(alert_threshold_hot=0.0010, alert_threshold_warm=0.0004)
    assert isinstance(detector.detector, FundingRegimeDetector)
    assert detector.alert_threshold_hot == 0.0010
    assert detector.alert_threshold_warm == 0.0004

def test_init_edge_case_empty_strings():
    with pytest.raises(TypeError):
        FundingMonitorDaemon(alert_threshold_hot="", alert_threshold_warm="")

def test_init_edge_case_none_values(fmd):
    detector = FundingMonitorDaemon(alert_threshold_hot=None, alert_threshold_warm=None)
    assert isinstance(detector.detector, FundingRegimeDetector)
    assert detector.alert_threshold_hot == 0.0010
    assert detector.alert_threshold_warm == 0.0004

def test_init_edge_case_invalid_file_path(fmd):
    fmd.alerts_file = 'invalid/path/funding_alerts.jsonl'
    with pytest.raises(FileNotFoundError):
        FundingMonitorDaemon()

def test_async_behavior(mocker, event_loop):
    class MockFundingRegimeDetector:
        async def detect(self):
            return "some_regime"

    mocker.patch('agents.funding_monitor_daemon.FundingRegimeDetector', new=MockFundingRegimeDetector)
    
    fmd = FundingMonitorDaemon()
    
    import asyncio

    result = event_loop.run_until_complete(asyncio.create_task(fmd.detector.detect()))
    assert result == "some_regime"