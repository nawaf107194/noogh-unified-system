import pytest

from unified_core.core.amla import AMLA, AttackSimulation


class MockAMLA(AMLA):
    def __init__(self):
        super().__init__()
        self._run_adversarial_injections = MagicMock()


def test_perf_adversarial_audit_happy_path():
    amla = MockAMLA()
    mock_request = MagicMock()
    expected_results = [AttackSimulation(), AttackSimulation()]
    amla._run_adversarial_injections.return_value = expected_results, True

    results, success = amla._perf_adversarial_audit(mock_request)

    assert results == expected_results
    assert success is True
    amla._run_adversarial_injections.assert_called_once_with(mock_request)


def test_perf_adversarial_audit_empty_request():
    amla = MockAMLA()
    mock_request = MagicMock()
    mock_request.is_empty.return_value = True

    results, success = amla._perf_adversarial_audit(mock_request)

    assert results == []
    assert success is False
    amla._run_adversarial_injections.assert_not_called()


def test_perf_adversarial_audit_none_request():
    amla = MockAMLA()
    mock_request = MagicMock()

    results, success = amla._perf_adversarial_audit(None)

    assert results == []
    assert success is False
    amla._run_adversarial_injections.assert_not_called()


def test_perf_adversarial_audit_boundary_values():
    amla = MockAMLA()
    mock_request = MagicMock()
    mock_request.is_empty.return_value = False
    mock_request.has_boundary_values.return_value = True

    results, success = amla._perf_adversarial_audit(mock_request)

    assert results == []
    assert success is False
    amla._run_adversarial_injections.assert_not_called()


def test_perf_adversarial_audit_invalid_input():
    amla = MockAMLA()
    mock_request = "not_a_request"

    results, success = amla._perf_adversarial_audit(mock_request)

    assert results == []
    assert success is False
    amla._run_adversarial_injections.assert_not_called()