import pytest

from unified_core.governance.feature_flags import FeatureFlags as FF

@pytest.mark.parametrize("flag_attr, expected_value", [
    ("GOVERNANCE_ENABLED", True),
    ("AUTH_GATE_ENABLED", False),
    ("APPROVAL_GATE_ENABLED", True),
    ("CIRCUIT_BREAKER_ENABLED", False),
    ("AUDIT_LOG_ENABLED", True),
    ("DRY_RUN", False),
    ("WRAP_PROCESS_SPAWN", True),
    ("WRAP_PROCESS_KILL", False),
    ("WRAP_FS_DELETE", True),
    ("WRAP_NETWORK_HTTP", False),
])
def test_get_status_happy_path(flag_attr, expected_value):
    setattr(FF, flag_attr, expected_value)
    status = FF.get_status()
    assert status[flag_attr] == expected_value

@pytest.mark.parametrize("flag_attr, expected_value", [
    ("GOVERNANCE_ENABLED", None),
    ("AUTH_GATE_ENABLED", None),
    ("APPROVAL_GATE_ENABLED", None),
    ("CIRCUIT_BREAKER_ENABLED", None),
    ("AUDIT_LOG_ENABLED", None),
    ("DRY_RUN", None),
    ("WRAP_PROCESS_SPAWN", None),
    ("WRAP_PROCESS_KILL", None),
    ("WRAP_FS_DELETE", None),
    ("WRAP_NETWORK_HTTP", None),
])
def test_get_status_edge_cases(flag_attr, expected_value):
    setattr(FF, flag_attr, expected_value)
    status = FF.get_status()
    assert status[flag_attr] == expected_value

@pytest.mark.parametrize("invalid_input, expected_output", [
    (None, {}),
    ("not a dict", {}),
    ([], {}),
])
def test_get_status_error_cases(invalid_input, expected_output):
    # Since the function does not explicitly raise errors for invalid inputs,
    # we will assert that the output is an empty dictionary.
    status = FF.get_status()
    assert status == expected_output