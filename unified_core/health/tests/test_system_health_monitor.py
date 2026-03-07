import pytest
from unittest.mock import patch, MagicMock
import time

from unified_core.health.system_health_monitor import SystemHealthMonitor
from unified_core.storage import Storage
from unified_core.pb.learning_pb2 import InnovationStatus

@pytest.fixture
def system_health_monitor():
    storage = MagicMock(spec=Storage)
    monitor = SystemHealthMonitor(storage)
    return monitor

@pytest.fixture
def innovations_data():
    return [
        {'status': InnovationStatus.INNOVATION_STATUS_APPLIED, 'applied_at': time.time()},
        {'status': InnovationStatus.INNOVATION_STATUS_APPLIED, 'applied_at': time.time() - 24 * 3600},
        {'status': InnovationStatus.INNOVATION_STATUS_PENDING, 'applied_at': None}
    ]

def test_check_innovation_application_rate_happy_path(system_health_monitor, innovations_data):
    storage = system_health_monitor.storage
    storage.get_all.return_value = innovations_data

    with patch('unified_core.health.system_health_monitor.time') as mock_time:
        mock_time.time.return_value = time.time() - 12 * 3600
        system_health_monitor._check_innovation_application_rate()

    assert not system_health_monitor.issues

def test_check_innovation_application_rate_edge_case_empty(system_health_monitor):
    storage = system_health_monitor.storage
    storage.get_all.return_value = []

    with patch('unified_core.health.system_health_monitor.time') as mock_time:
        mock_time.time.return_value = time.time() - 12 * 3600
        system_health_monitor._check_innovation_application_rate()

    assert not system_health_monitor.issues

def test_check_innovation_application_rate_edge_case_none(system_health_monitor):
    storage = system_health_monitor.storage
    storage.get_all.return_value = None

    with patch('unified_core.health.system_health_monitor.time') as mock_time:
        mock_time.time.return_value = time.time() - 12 * 3600
        system_health_monitor._check_innovation_application_rate()

    assert not system_health_monitor.issues

def test_check_innovation_application_rate_edge_case_boundary(system_health_monitor, innovations_data):
    storage = system_health_monitor.storage
    storage.get_all.return_value = innovations_data

    with patch('unified_core.health.system_health_monitor.time') as mock_time:
        mock_time.time.return_value = time.time() - 24 * 3600 + 1
        system_health_monitor._check_innovation_application_rate()

    assert not system_health_monitor.issues

def test_check_innovation_application_rate_error_case_invalid_input(system_health_monitor):
    storage = system_health_monitor.storage
    storage.get_all.return_value = [{'status': 'invalid_status', 'applied_at': time.time()}]

    with patch('unified_core.health.system_health_monitor.time') as mock_time:
        mock_time.time.return_value = time.time() - 12 * 3600
        system_health_monitor._check_innovation_application_rate()

    assert not system_health_monitor.issues

def test_check_innovation_application_rate_error_case_no_storage_file(system_health_monitor):
    storage = system_health_monitor.storage
    storage.get_all.return_value = None
    storage.pb_file.exists.return_value = False

    with patch('unified_core.health.system_health_monitor.time') as mock_time:
        mock_time.time.return_value = time.time() - 12 * 3600
        system_health_monitor._check_innovation_application_rate()

    assert not system_health_monitor.issues